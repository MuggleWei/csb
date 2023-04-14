import logging
import os
import selectors
import subprocess


class CommandHandle:
    def __init__(self):
        self._workflow_fp = None
        self._command_logger = logging.getLogger("command")

    def set_fp(self, fp):
        self._workflow_fp = fp

    def exec(self, command):
        """
        exec command
        """
        logging.debug("exec command: {}".format(command))
        if self._workflow_fp is not None:
            self._workflow_fp.write("COMMAND|{}\n".format(command))

        pos = command.find("cd ")
        if pos != -1:
            chpath = command[pos+2:].strip()
            chpath = chpath.strip("\"")
            if not os.path.isabs(chpath):
                chpath = os.path.join(os.getcwd(), chpath)
            os.chdir(chpath)
            return True

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
        exec subporcess
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
                    if self._workflow_fp is not None:
                        self._workflow_fp.write("INFO|{}\n".format(data))
                    self._command_logger.info("{}".format(data))
                elif key.fileobj is p.stderr:
                    if self._workflow_fp is not None:
                        self._workflow_fp.write("ERROR|{}\n".format(data))
                    self._command_logger.error("{}".format(data))
                self._workflow_fp.flush()
