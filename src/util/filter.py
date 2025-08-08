class Filter:
    def __init__(self, key, values, id_field):
        """
        Initialize the Filter class.
        
        :param key: The key field to filter on
        :param values: A list of strings to match against the key's value
        :param id_field: The field whose value should be appended to the filtered list
        """
        self.key = key
        self.values = values
        self.id_field = id_field

    def do_filter(self, items):
        """
        Filter a list of items based on the key and values.
        
        :param items: A list of dictionaries to filter
        :return: A filtered list containing only the id_field values
        """
        filtered_items = []

        for item in items:
            if isinstance(item, dict) and self.key in item:
                # Check if item[self.key] is a list and has at least one value in self.values
                if isinstance(item[self.key], list) and any(value in self.values for value in item[self.key]):
                    if self.id_field in item:
                        filtered_items.append(item[self.id_field])

        return filtered_items