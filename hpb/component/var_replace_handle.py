import re
import typing


class VarReplaceHandle:
    @classmethod
    def replace(cls, content, replace_dict: typing.Dict):
        """
        replace variable in content
        :param content: variable value
        :param replace_dict: current variable replace dict
        """
        content = str(content)
        finds = re.findall(r'\${\w+}', content)
        finds_set = set(finds)
        if len(finds_set) == 0:
            return content
        for var in finds_set:
            var_name = var[2:-1]
            if var_name not in replace_dict:
                return None
            content = content.replace(var, replace_dict[var_name])
        return content

    @classmethod
    def replace_list(
            cls,
            var_list: typing.List[typing.Dict], replace_dict: typing.Dict,
            result_add_to_var=True, result_add_to_replace=True,
            replace_override=False):
        """
        replace all variable in var_dict
        :param var_list: replace target list
        :param replace_dict: variable dict
        :param result_add_to_var: result add into var_dict
        :param result_add_to_replace: result add into replace_dict
        :param replace_override: if var already exists in replace, need override
        :return:
            - True: all variable be replaced
            - False: some variable not be replaced
        """
        all_replaced = True
        for var in var_list:
            for k in var.keys():
                v = var[k]
                v = VarReplaceHandle.replace(v, replace_dict)
                if v is None:
                    all_replaced = False
                    continue

                if result_add_to_var:
                    var[k] = v

                if k in replace_dict and replace_override is False:
                    continue
                if result_add_to_replace:
                    replace_dict[k] = v
        return all_replaced
