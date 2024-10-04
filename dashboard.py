import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency

sns.set(style='dark')

def create_daily_orders(df):
    daily_order_df = df.resample(rule='D', on='shipping_limit_date').agg({
        "order_id": "nunique",
        "price": "sum"
    })
    daily_order_df = daily_order_df.reset_index()
    daily_order_df.rename(columns={
        "order_id": "order_count",
        "price": "revenue"
    }, inplace=True)
    return daily_order_df

def create_sum_order_items(df):
    sum_order_items_df = df.groupby("product_category_name").order_item_id.sum().sort_values(ascending=False).reset_index()
    return sum_order_items_df

def create_byprice(df):
    byprice_df = df.groupby("price").seller_id.nunique().reset_index()
    byprice_df.rename(columns={
        "seller_id": "seller_count"
    }, inplace=True)
    return byprice_df

def create_byorder_item_id(df):
    byorder_item_id_df = df.groupby("order_item_id").seller_id.nunique().reset_index()
    byorder_item_id_df.rename(columns={
        "seller_id": "seller_count"
    }, inplace=True)
    return byorder_item_id_df

def create_rfm(df):
    rfm_df = df.groupby(by="seller_id", as_index=False).agg({
        "shipping_limit_date": "max", 
        "order_id": "nunique", 
        "price": "sum" 
    })

    rfm_df.columns = ["seller_id", "max_order_timestamp", "frequency", "monetary"]

    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"].dt.date
    recent_date = df["shipping_limit_date"].dt.date.max() 
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days)
    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)

    return rfm_df

all_df = pd.read_csv("order_products_dataset.csv")

datetime_columns = ["shipping_limit_date"]
all_df.sort_values(by="shipping_limit_date", inplace=True)
all_df.reset_index(inplace=True)

for column in datetime_columns:
    all_df[column] = pd.to_datetime(all_df[column])

min_date = all_df["shipping_limit_date"].min().date() 
max_date = all_df["shipping_limit_date"].max().date()

with st.sidebar:
    st.image("logo-png.png")

    start_date, end_date = st.date_input(
        label='Rentang Waktu', min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)

main_df = all_df[(all_df["shipping_limit_date"] >= start_date) & 
                 (all_df["shipping_limit_date"] <= end_date)]

daily_order_df = create_daily_orders(main_df)
sum_order_items_df = create_sum_order_items(main_df)
byprice_df = create_byprice(main_df)
byorder_item_id_df = create_byorder_item_id(main_df)
rfm_df = create_rfm(main_df)

# Header
st.header(":sparkles: Ayu Market Dashboard :sparkles:")

st.subheader('Daily Orders')
col1, col2 = st.columns(2)

with col1:
    total_orders = daily_order_df.order_count.sum()
    st.metric("Total Order", value=total_orders)

with col2:
    total_revenue = format_currency(daily_order_df.revenue.sum(), "AUD", locale='es_CO')
    st.metric("Total Revenue", value=total_revenue)

# Daily Orders Visualization
fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(
    daily_order_df["shipping_limit_date"],
    daily_order_df["order_count"],
    marker='o',
    linewidth=2,
    color="#0D47A1"  # Dark blue
)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)
st.pyplot(fig)

# Sum of Order Items by Product Category
st.subheader('Order Items by Product Category')
fig, ax = plt.subplots(figsize=(16, 8))
sns.barplot(
    x='order_item_id',
    y='product_category_name',
    data=sum_order_items_df,
    palette='Blues_d',
    ax=ax
)
ax.set_xlabel('Total Order Items', fontsize=14)
ax.set_ylabel('Product Category', fontsize=14)
ax.set_title('Sum of Order Items by Product Category', fontsize=18)
st.pyplot(fig)

# Sellers Count by Price
st.subheader('Number of Sellers by Price')
fig, ax = plt.subplots(figsize=(16, 8))
sns.barplot(
    x='price',
    y='seller_count',
    data=byprice_df,
    palette='Purples_d',
    ax=ax
)
ax.set_xlabel('Price', fontsize=14)
ax.set_ylabel('Unique Sellers', fontsize=14)
ax.set_title('Number of Sellers by Price', fontsize=18)
st.pyplot(fig)

# Sellers Count by Order Item ID
st.subheader('Number of Sellers by Order Item ID')
fig, ax = plt.subplots(figsize=(16, 8))
sns.barplot(
    x='order_item_id',
    y='seller_count',
    data=byorder_item_id_df,
    palette='Greens_d',
    ax=ax
)
ax.set_xlabel('Order Item ID', fontsize=14)
ax.set_ylabel('Unique Sellers', fontsize=14)
ax.set_title('Number of Sellers by Order Item ID', fontsize=18)
st.pyplot(fig)

# RFM Analysis
st.subheader('RFM Analysis')
fig, ax = plt.subplots(figsize=(16, 8))
sns.scatterplot(
    x='recency',
    y='monetary',
    size='frequency',
    data=rfm_df,
    palette='coolwarm',
    ax=ax,
    sizes=(20, 200),
    legend=False
)
ax.set_xlabel('Recency (days since last order)', fontsize=14)
ax.set_ylabel('Monetary Value (Total Spending)', fontsize=14)
ax.set_title('RFM Analysis', fontsize=18)
st.pyplot(fig)

main_df['year_month'] = main_df['shipping_limit_date'].dt.to_period('M')
monthly_sales_df = main_df.groupby('year_month').agg({
    'price': 'sum'
}).reset_index()

max_sales_row = monthly_sales_df[monthly_sales_df['price'] == monthly_sales_df['price'].max()]

st.subheader('Penjualan Produk Tertinggi Berdasarkan Bulan dan Tahun')
st.write(f"<span style='color: #FF5733;'>Penjualan produk mencapai puncaknya pada bulan {max_sales_row['year_month'].values[0]} dengan total penjualan AUD {format_currency(max_sales_row['price'].values[0], 'AUD', locale='es_CO')}</span>", unsafe_allow_html=True)

fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(
    monthly_sales_df["year_month"].astype(str),
    monthly_sales_df["price"],
    marker='o',
    linewidth=2,
    color="#0D47A1"
)
ax.set_xlabel('Bulan-Tahun', fontsize=14)
ax.set_ylabel('Total Penjualan (AUD)', fontsize=14)
ax.set_title('Penjualan Bulanan', fontsize=18)
ax.tick_params(axis='x', labelrotation=45)
st.pyplot(fig)
