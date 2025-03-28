import streamlit as st
import pandas as pd

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='Heat stress monitoring',
)


'''
# Delta LAB
#### Heat stress monitoring app
Tecnológico de Costa Rica
'''

entrada = pd.read_csv("dashboard/entradas.csv").fillna("")

# type = st.selectbox(
#     'Type',
#     types
# )

# subtypes = detail[detail["type"]==type]["subtype"].unique()

# subtype = st.selectbox(
#     'Subtype',
#     subtypes
# )

# list = detail[(detail["type"]==type) & (detail["subtype"]==subtype)]

# list = list.merge(locati, on='code', how='left')

# list.drop(columns=["info","type","subtype"],inplace=True)

st.markdown("### Detalles:")

st.dataframe(entrada,hide_index=True)  