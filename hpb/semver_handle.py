import typing


class SemverHandle:
    @classmethod
    def parse(cls, tag) -> typing.Optional[typing.List]:
        """
        check tag is semver
        semver format
        e.g.
            1.0.1, v1.0.1, 1.0.1-alpha

        :param tag: version info
        :return: list [major, minor, patch, pre_release]
        """
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
        if len(ver_infos) != 3:
            return None

        semver = []
        for v in ver_infos:
            if not v.isdigit():
                return None
            semver.append(int(v))
        semver.append(pre_release)

        return semver

    @classmethod
    def compare(cls, v1, v2):
        """
        compare two semver
        if v1 > v2: return 1
        if v1 == v2: return 0
        if v1 < v2: return -1
        :param v1: result of SemverHandle.parse
        :param v2: result of SemverHandle.parse
        """
        if v1[0] > v2[0]:
            return 1
        elif v1[0] < v2[0]:
            return -1

        if v1[1] > v2[1]:
            return 1
        elif v1[1] < v2[1]:
            return -1

        if v1[2] > v2[2]:
            return 1
        elif v1[2] < v2[2]:
            return -1

        return cls.compare_pre_release(v1[3], v2[3])

    @classmethod
    def compare_pre_release(cls, pre1, pre2):
        """
        compare pre release
        """
        if len(pre1) == 0 and len(pre2) != 0:
            return 1
        if len(pre1) != 0 and len(pre2) == 0:
            return -1
        if len(pre1) == 0 and len(pre2) == 0:
            return 0

        pv1 = cls.split_pre_release(pre1)
        pv2 = cls.split_pre_release(pre2)

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

    @classmethod
    def split_pre_release(cls, pre):
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
