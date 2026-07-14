import pandas as pd

class XMLAdpater:
    column_names = ['Customer ID', 'Age', 'Gender', 'Item Purchased', 'Category',
       'Purchase Amount (USD)', 'Location', 'Size', 'Color', 'Season',
       'Review Rating', 'Subscription Status', 'Shipping Type',
       'Discount Applied', 'Promo Code Used', 'Previous Purchases',
       'Payment Method', 'Frequency of Purchases', 'year']

    def __init__(self, xml_data_path):
        self.xml_data_path = xml_data_path

    def get_data(self):
        df = pd.read_xml(self.xml_data_path)
        df.columns = self.column_names
        return df