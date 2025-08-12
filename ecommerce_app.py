import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Set page configuration
st.set_page_config(
    page_title="E-Commerce Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load sample data (in a real app, this would connect to a database)
@st.cache_data
def load_data():
    # Generate sample sales data
    np.random.seed(42)
    date_range = pd.date_range(start='2023-01-01', end='2023-12-31')
    products = ['Laptop', 'Phone', 'Tablet', 'Headphones', 'Smartwatch', 'Camera']
    categories = ['Electronics', 'Electronics', 'Electronics', 'Accessories', 'Accessories', 'Electronics']
    regions = ['North', 'South', 'East', 'West']
    
    data = []
    for date in date_range:
        for _ in range(np.random.randint(5, 20)):
            product_idx = np.random.randint(0, len(products))
            price = np.random.uniform(100, 2000)
            quantity = np.random.randint(1, 3)
            region = np.random.choice(regions)
            discount = np.random.choice([0, 0.05, 0.1, 0.15, 0.2], p=[0.5, 0.2, 0.15, 0.1, 0.05])
            
            data.append({
                'Date': date,
                'Product': products[product_idx],
                'Category': categories[product_idx],
                'Price': price,
                'Quantity': quantity,
                'Revenue': price * quantity * (1 - discount),
                'Discount': discount,
                'Region': region,
                'CustomerID': np.random.randint(1000, 9999)
            })
    
    df = pd.DataFrame(data)
    
    # Generate customer data
    customer_ids = df['CustomerID'].unique()
    customer_data = []
    for cust_id in customer_ids:
        customer_data.append({
            'CustomerID': cust_id,
            'Age': np.random.randint(18, 70),
            'Gender': np.random.choice(['Male', 'Female']),
            'JoinDate': np.random.choice(pd.date_range(start='2022-01-01', end='2023-01-01')),
            'LoyaltyTier': np.random.choice(['Bronze', 'Silver', 'Gold'], p=[0.6, 0.3, 0.1])
        })
    
    customer_df = pd.DataFrame(customer_data)
    
    return df, customer_df

sales_df, customer_df = load_data()

# Merge data
merged_df = pd.merge(sales_df, customer_df, on='CustomerID', how='left')

# Sidebar filters
st.sidebar.header("Filters")
date_range = st.sidebar.date_input(
    "Date range",
    value=[datetime(2023, 1, 1), datetime(2023, 12, 31)],
    min_value=datetime(2023, 1, 1),
    max_value=datetime(2023, 12, 31)
)

if len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = merged_df[(merged_df['Date'] >= pd.to_datetime(start_date)) & 
                           (merged_df['Date'] <= pd.to_datetime(end_date))]
else:
    filtered_df = merged_df.copy()

selected_categories = st.sidebar.multiselect(
    "Categories",
    options=filtered_df['Category'].unique(),
    default=filtered_df['Category'].unique()
)

selected_products = st.sidebar.multiselect(
    "Products",
    options=filtered_df['Product'].unique(),
    default=filtered_df['Product'].unique()
)

selected_regions = st.sidebar.multiselect(
    "Regions",
    options=filtered_df['Region'].unique(),
    default=filtered_df['Region'].unique()
)

# Apply filters
filtered_df = filtered_df[
    (filtered_df['Category'].isin(selected_categories)) &
    (filtered_df['Product'].isin(selected_products)) &
    (filtered_df['Region'].isin(selected_regions))
]

# Main dashboard
st.title("📊 E-Commerce Analytics Dashboard")
st.markdown("""
    Interactive dashboard for analyzing e-commerce performance metrics.
    Use the filters in the sidebar to customize the data view.
""")

# KPI cards
col1, col2, col3, col4 = st.columns(4)
with col1:
    total_revenue = filtered_df['Revenue'].sum()
    st.metric("Total Revenue", f"${total_revenue:,.2f}")

with col2:
    total_orders = len(filtered_df)
    st.metric("Total Orders", f"{total_orders:,}")

with col3:
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    st.metric("Avg. Order Value", f"${avg_order_value:,.2f}")

with col4:
    unique_customers = filtered_df['CustomerID'].nunique()
    st.metric("Unique Customers", f"{unique_customers:,}")

# Tabs for different sections
tab1, tab2, tab3, tab4 = st.tabs(["Sales Overview", "Product Analysis", "Customer Insights", "Geographic View"])

with tab1:
    st.subheader("Sales Trend")
    
    # Daily/Weekly/Monthly selector
    time_group = st.radio(
        "Time grouping",
        ["Daily", "Weekly", "Monthly"],
        horizontal=True
    )
    
    if time_group == "Daily":
        time_format = "%Y-%m-%d"
        group_col = 'Date'
    elif time_group == "Weekly":
        time_format = "%Y-%U"
        group_col = filtered_df['Date'].dt.strftime(time_format)
    else:  # Monthly
        time_format = "%Y-%m"
        group_col = filtered_df['Date'].dt.strftime(time_format)
    
    sales_trend = filtered_df.groupby(group_col)['Revenue'].sum().reset_index()
    
    fig = px.line(
        sales_trend,
        x=group_col,
        y='Revenue',
        title=f"{time_group} Sales Trend",
        labels={'Revenue': 'Revenue ($)', group_col: 'Date'},
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Revenue by category
    st.subheader("Revenue by Category")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        category_revenue = filtered_df.groupby('Category')['Revenue'].sum().reset_index()
        fig = px.pie(
            category_revenue,
            names='Category',
            values='Revenue',
            hole=0.3,
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.dataframe(
            category_revenue.sort_values('Revenue', ascending=False),
            hide_index=True,
            use_container_width=True
        )

with tab2:
    st.subheader("Product Performance")
    
    # Top products by revenue
    top_products = filtered_df.groupby('Product').agg({
        'Revenue': 'sum',
        'Quantity': 'sum',
        'Discount': 'mean'
    }).sort_values('Revenue', ascending=False).reset_index()
    
    fig = px.bar(
        top_products,
        x='Product',
        y='Revenue',
        color='Product',
        title="Revenue by Product",
        labels={'Revenue': 'Revenue ($)'},
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Product metrics
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Units Sold by Product")
        fig = px.bar(
            top_products,
            x='Product',
            y='Quantity',
            color='Product',
            labels={'Quantity': 'Units Sold'},
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Average Discount by Product")
        fig = px.bar(
            top_products,
            x='Product',
            y='Discount',
            color='Product',
            labels={'Discount': 'Avg. Discount'},
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Customer Demographics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Age distribution
        fig = px.histogram(
            filtered_df.drop_duplicates('CustomerID'),
            x='Age',
            nbins=20,
            title="Customer Age Distribution",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Gender distribution
        gender_dist = filtered_df.drop_duplicates('CustomerID')['Gender'].value_counts().reset_index()
        fig = px.pie(
            gender_dist,
            names='Gender',
            values='count',
            title="Customer Gender Distribution",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Loyalty Tier Analysis")
    
    loyalty_metrics = filtered_df.groupby('LoyaltyTier').agg({
        'CustomerID': 'nunique',
        'Revenue': 'sum',
        'Discount': 'mean'
    }).reset_index()
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(
            loyalty_metrics,
            x='LoyaltyTier',
            y='CustomerID',
            color='LoyaltyTier',
            title="Customers by Loyalty Tier",
            labels={'CustomerID': 'Number of Customers'},
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.bar(
            loyalty_metrics,
            x='LoyaltyTier',
            y='Revenue',
            color='LoyaltyTier',
            title="Revenue by Loyalty Tier",
            labels={'Revenue': 'Total Revenue ($)'},
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.subheader("Regional Performance")
    
    region_metrics = filtered_df.groupby('Region').agg({
        'Revenue': 'sum',
        'CustomerID': 'nunique',
        'Quantity': 'sum'
    }).reset_index()
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(
            region_metrics,
            x='Region',
            y='Revenue',
            color='Region',
            title="Revenue by Region",
            labels={'Revenue': 'Total Revenue ($)'},
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.bar(
            region_metrics,
            x='Region',
            y='CustomerID',
            color='Region',
            title="Customers by Region",
            labels={'CustomerID': 'Number of Customers'},
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Map visualization (simplified)
    st.subheader("Regional Distribution")
    
    # Create a simple map with region centers (in a real app, you'd use actual coordinates)
    region_coords = {
        'North': {'lat': 40, 'lon': -100},
        'South': {'lat': 30, 'lon': -100},
        'East': {'lat': 35, 'lon': -75},
        'West': {'lat': 35, 'lon': -120}
    }
    
    map_df = region_metrics.copy()
    map_df['lat'] = map_df['Region'].map(lambda x: region_coords[x]['lat'])
    map_df['lon'] = map_df['Region'].map(lambda x: region_coords[x]['lon'])
    
    fig = px.scatter_geo(
        map_df,
        lat='lat',
        lon='lon',
        size='Revenue',
        color='Region',
        hover_name='Region',
        hover_data=['Revenue', 'CustomerID'],
        projection='natural earth',
        title="Revenue by Region",
        height=500
    )
    
    fig.update_geos(
        visible=False,
        showcountries=True,
        showcoastlines=True,
        showland=True,
        fitbounds="locations"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    


# Raw data view
st.sidebar.header("Data Export")
if st.sidebar.checkbox("Show raw data"):
    st.subheader("Raw Data Preview")
    st.dataframe(filtered_df.head(100), use_container_width=True)
    
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button(
        "Download as CSV",
        data=csv,
        file_name="ecommerce_data.csv",
        mime="text/csv"
    )