class SemverItem:
    def __init__(self):
        self.major = 0
        self.minor = 0
        self.patch = 0
        self.pre_release = ""

    def load(self, tag):
        """
        load semver str
        """
        tag = tag.strip()
        if tag.startswith("v"):
            tag = tag[1:]
        idx = tag.find("-")
        if idx == -1:
            ver = tag
            pre_release = ""
        else:
            ver = tag[:idx]
            pre_release = tag[idx + 1:]

        ver_infos = ver.split(".")
        if len(ver_infos) > 3:
            return False

        semver = []
        for v in ver_infos:
            if not v.isdigit():
                return False
            semver.append(int(v))

        self.major = semver[0]
        if len(semver) > 1:
            self.minor = semver[1]
        if len(semver) > 2:
            self.patch = semver[2]
        self.pre_release = pre_release

        return True

    def compare(self, other):
        """
        compare two semver
        if self > other: return 1
        if self == other: return 0
        if self < other: return -1
        """
        if self.major > other.major:
            return 1
        elif self.major < other.major:
            return -1

        if self.minor > other.minor:
            return 1
        elif self.minor < other.minor:
            return -1

        if self.patch > other.patch:
            return 1
        elif self.patch < other.patch:
            return -1

        return self._compare_pre_release(other)

    def _compare_pre_release(self, other):
        """
        compare pre release
        """
        pre1 = self.pre_release
        pre2 = other.pre_release

        if len(pre1) == 0 and len(pre2) != 0:
            return 1
        if len(pre1) != 0 and len(pre2) == 0:
            return -1
        if len(pre1) == 0 and len(pre2) == 0:
            return 0

        pv1 = self._split_pre_release(pre1)
        pv2 = self._split_pre_release(pre2)

        pre_release_dict = {
            "alpha": 0,
            "beta": 1,
            "rc": 2,
        }
        p1 = pre_release_dict.get(pv1[0], -1)
        p2 = pre_release_dict.get(pv2[0], -1)

        if p1 > p2:
            return 1
        elif p1 < p2:
            return -1

        if pv1[1] > pv2[1]:
            return 1
        elif pv1[1] < pv2[1]:
            return -1

        return 0

    def _split_pre_release(self, pre):
        """
        split pre-release into list[alpha, ver]
        e.g.
            alpha.1 -> [alpha, 1]
            beta.11 -> [beta, 11]
            beta -> [beta, 0]
        """
        pv = pre.split(".")
        if len(pv) > 1:
            v = pv[1]
        else:
            v = "0"

        if v.isdigit():
            v = int(v)
        else:
            v = 0

        return [pv[0], v]
