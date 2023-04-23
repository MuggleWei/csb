import logging
import os
import selectors
import subprocess

from hpb.utils.singleton import singleton
from threading import Thread


@singleton
class CommandHandle:
    def __init__(self):
        self._command_logger = logging.getLogger("command")

    def exec(self, command):
        """
        exec command
        """
        command = command.strip()
        logging.debug("exec command: {}".format(command))
        self._command_logger.info("REAL_COMMAND|{}".format(command))

        pos = command.find("cd ")
        if pos == 0:
            chpath = command[pos+2:].strip()
            chpath = chpath.strip("\"")
            if not os.path.isabs(chpath):
                chpath = os.path.join(os.getcwd(), chpath)
            os.chdir(chpath)
            return True

        # join multiple line and remove '\$' for windows
        command = command.replace("\\\r\n", "")
        command = command.replace("\\\n", "")
        command = command.replace("\\\r", "")

        p = subprocess.Popen(
            command, shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        try:
            self._exec_subporcess(p)
            p.communicate()
            if p.returncode is not None and p.returncode != 0:
                logging.error("failed exec: {}, ret code: {}".format(
                    command, p.returncode))
                return False
        except Exception as e:
            logging.warning("wait subprocess finish except: {}".format(e))
            p.terminate()
            return False
        return True

    def _exec_subporcess(self, p):
        """
        exec subprocess
        :param p: subprocess
        """
        # NOTE: windows not support select fileno
        # self._exec_subprocess_with_select(p)
        self._exec_subprocess_with_wait_threads(p)

    def _exec_subprocess_with_wait_threads(self, p):
        """
        exec subprocess with wait thread
        """
        threads = []
        threads.append(self._tee(p.stdout, "INFO"))
        threads.append(self._tee(p.stderr, "ERROR"))
        for t in threads:
            t.join()

    def _tee(self, infile, filetype):
        """
        tee subprocess output
        """
        def fanout(infile, filetype):
            for line in iter(infile.readline, b""):
                decode_failed = False
                try:
                    data = line.decode("utf-8")
                except Exception:
                    decode_failed = True

                if decode_failed is True:
                    try:
                        data = line.decode("gb18030")
                    except Exception:
                        data = "*** failed decode ***"

                data = data.strip()
                if filetype == "INFO":
                    self._command_logger.info("{}".format(data))
                else:
                    self._command_logger.error("{}".format(data))

        t = Thread(target=fanout, args=(infile, filetype))
        t.daemon = True
        t.start()
        return t

    def _exec_subprocess_with_select(self, p):
        """
        exec subprocess in *nix
        :param p: subprocess
        """
        sel = selectors.DefaultSelector()
        sel.register(p.stdout, selectors.EVENT_READ)
        sel.register(p.stderr, selectors.EVENT_READ)
        while True:
            for key, _ in sel.select():
                data = key.fileobj.read1().decode()
                if not data:
                    return
                data = data.strip()
                if key.fileobj is p.stdout:
                    self._command_logger.info("{}".format(data))
                elif key.fileobj is p.stderr:
                    self._command_logger.error("{}".format(data))
