import sys
import yaml
import csv


def read_yaml_file(filename, load_all=False):
    with open(filename, mode='r') as f:
        if not load_all:
            yaml_data = yaml.load(f, Loader=yaml.FullLoader)
        else:
            # convert generator to list before returning
            yaml_data = list(yaml.load_all(f, Loader=yaml.FullLoader))
    return yaml_data


def read_csv_file(filename):
    with open(filename, mode='r') as csv_file:
        csv_row_dict_list = list()  # list of key-value pairs produced from every CSV row except header
        # if header contains __CCvar and __CCvalue CSV will be processed vertically
        # each row will be treated as separate variable with a name of __CCvar
        vars_from_csv = dict()
        for row in csv.DictReader(csv_file):
            updated_row_dict = dict()
            for k, v in row.items():
                # remove potential spaces left and right
                k = k.strip()
                if v:
                    v = v.strip()
                updated_row_dict.update({k: v})
            if '__CCkey' in updated_row_dict.keys():
                if not '__CCvalue' in updated_row_dict.keys():
                    sys.exit(
                        f'ERROR: __CCkey is defined without __CCvalue in {csv_file}')
                vars_from_csv.update({updated_row_dict['__CCkey']: updated_row_dict['__CCvalue']})
            else:
                csv_row_dict_list.append(updated_row_dict)

    if len(csv_row_dict_list):
        return csv_row_dict_list
    else:
        return vars_from_csv


def smart_update(target_dict: dict, target_value_path: str, source_dict: dict, source_key: str, convert_to='str', mandatory=False) -> dict:
    """This function is doing some basic verification of values from CSV files.
    Feel free to add additional logic if required.

    Args:
        target_dict (dict): dictionary to update
        target_value_path (str): path to the value to be set, separated with '.'. For ex.: key1.key2
        source_dict (dict): An origin dictionary
        source_key (str): The value to be verified
        convert_to (str, optional): Convert original text value to the specified type. Possible types: ['int', 'str']. Defaults to 'str'.
        mandatory (bool, optional): True is value is mandatory. Defaults to False.

    Returns:
        dict: Returns target dictionary
    """

    # check if header is defined in the CSV
    if source_key not in source_dict.keys():
        if mandatory:
            sys.exit(
                f'ERROR: {source_key} field is mandatory and must be defined in the CSV file'
            )
    # check if the value is defined in the CSV
    elif not source_dict[source_key]:
        if mandatory:
            sys.exit(
                f'ERROR: {source_key} has an empty value. It is mandatory and must be defined in the CSV file'
            )
    else:
        if convert_to == 'int':
            source_value = int(source_dict[source_key])
        elif convert_to == 'str':
            source_value = source_dict[source_key]
        else:
            source_value = ''

        if source_value:

            path_keys = target_value_path.split('.')
            target_dict_stack = [target_dict]
            for k in path_keys:
                last_dict_in_stack = target_dict_stack[-1]
                if k in last_dict_in_stack.keys():
                    target_dict_stack.append({k: last_dict_in_stack[k]})
                else:
                    target_dict_stack.append({k: dict()})
            while path_keys:
                k = path_keys.pop()
                last_dict_in_stack = target_dict_stack.pop()
                if isinstance(source_value, dict):
                    last_dict_in_stack[k].update(source_value)
                else:
                    last_dict_in_stack.update({k: source_value})
                source_value = last_dict_in_stack
            
            target_dict.update(source_value)

        return target_dict
