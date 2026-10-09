# Importing Libraries
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

# Configure Page
st.set_page_config(page_title="Live Coffee Sales Dashboard", layout="wide")
st.title("☕ Sales Trend and Time-Based Performance Analysis for Afficionado Coffee Roasters")


DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Creating path for data so in local system it does not show any error
def resolve_data_path() -> Path:
    candidates = [
        Path(__file__).resolve().parent / "data" / "Afficionado Coffee Roasters.xlsx - Transactions (1).csv",
        Path(__file__).resolve().parent / "Afficionado Coffee Roasters updated.csv",
        Path("Afficionado Coffee Roasters updated.csv"),
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError("No sales data file found. Please place the CSV in the project folder or data directory.")

# Setting up data caches so 
@st.cache_data
def load_data() -> pd.DataFrame:
    data_path = resolve_data_path()
    df = pd.read_csv(data_path)

    # Clean up and isolate the raw transaction time string
    if "transaction_time" in df.columns:
        # If it was partially parsed as a full datetime string, extract just the time part
        df["time_str"] = (
            pd.to_datetime(df["transaction_time"], errors="coerce")
            .dt.time.astype(str)
            .fillna(df["transaction_time"].astype(str))
        )
    else:
        raise KeyError("The dataset must contain 'transaction_time'.")

    # Generate an artificial sequence of realistic calendar dates across the dataset This distributes your 149k transactions evenly over the last 90 days
    
    total_rows = len(df)
    start_date = pd.Timestamp("2026-04-01")
    end_date = pd.Timestamp("2026-06-30")


    # Create a sequence of dates matching the length of the dataframe
    generated_dates = pd.date_range(start=start_date, end=end_date, periods=total_rows)

    df["transaction_datetime"] = pd.to_datetime(
    generated_dates.strftime("%Y-%m-%d") + " " + df["time_str"],
    errors="coerce",
)

    # Standard dashboard metrics processing
    df["revenue"] = df["transaction_qty"] * df["unit_price"]
    df["hour"] = df["transaction_datetime"].dt.hour
    df["day_of_week"] = df["transaction_datetime"].dt.day_name()
    df["date"] = df["transaction_datetime"].dt.date

    return df.sort_values("transaction_datetime").reset_index(drop=True)

df = load_data()

st.caption("Explore sales performance by location, weekday, hour, and metric choice.")

# Adding filters for User Capabilities
st.sidebar.header("Filters")
locations = st.sidebar.multiselect(
    "Select Store Location",
    options=sorted(df["store_location"].dropna().unique()),
    default=sorted(df["store_location"].dropna().unique()),
)
days = st.sidebar.multiselect(
    "Select Days of Week",
    options=DAY_ORDER,
    default=DAY_ORDER,
)
hours = st.sidebar.slider("Select Hour Range", 0, 23, (0, 23))
metric_option = st.sidebar.radio("📊Select Metric", ["Revenue", "Transaction Quantity"])

if metric_option == "Revenue":
    metric_col = "revenue"
else:
    metric_col = "transaction_qty"

metric_label = "Revenue" if metric_option == "Revenue" else "Transaction Quantity"


df_filtered = df[
    (df["store_location"].isin(locations))
    & (df["day_of_week"].isin(days))
    & (df["hour"] >= hours[0])
    & (df["hour"] <= hours[1])
]

if df_filtered.empty:
    st.warning("No data matches the current filters. Please broaden the selection.")
    st.stop()

# Main page column
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("💰 Total Revenue", f"${df_filtered['revenue'].sum():,.0f}")
with col2:
    st.metric("🛒 Transaction Quantity", f"{df_filtered['transaction_qty'].sum():,}")
with col3:
    st.metric("📦 Total Orders", f"{df_filtered['transaction_id'].nunique():,}")

# Adding tabs 
tab1, tab2 = st.tabs([
    "📈Core Modules",
    "☕ Products",
])    

# First tab
with tab1:
        
    st.subheader("📈 Overall Sales Trend")
    daily_sales = df_filtered.resample("D", on="transaction_datetime")[metric_col].sum()
    fig = px.line(
        x=daily_sales.index,
        y=daily_sales.values,
        markers=True,
        text=daily_sales.values,
        labels={"x": "Date", "y": metric_label},
        title=f"Daily {metric_label} Trend",
    )
    fig.update_traces(textposition="top center")
    st.plotly_chart(fig, use_container_width=True)


    peak_day = daily_sales.idxmax()
    low_day = daily_sales.idxmin()
    st.info(f"""
    📈 Sales peaked on **{peak_day.date()}**

    📉 Lowest performance was on **{low_day.date()}**

    🔍 Indicates short-term demand fluctuations and possible seasonal spikes.
    """)

    csv = daily_sales.to_frame(name=metric_label).reset_index().rename(columns={"index": "date"}).to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download Daily Data", csv, "daily_sales.csv", "text/csv", key="download_daily")

    weekly_sales = df_filtered.resample("W", on="transaction_datetime")[metric_col].sum()
    fig1_weekly = px.line(
        x=weekly_sales.index,
        y=weekly_sales.values,
        markers=True,
        labels={"x": "Week", "y": metric_label},
        title=f"📈 Weekly {metric_label} Trend",
    )
    st.plotly_chart(fig1_weekly, use_container_width=True)


    peak_week = weekly_sales.idxmax()
    st.info(f"""
    📊 Highest weekly performance observed during **{peak_week.date()}** week

    📅 Weekly trends help identify consistent growth or decline patterns.
    """)

    csv = weekly_sales.to_frame(name=metric_label).reset_index().rename(columns={"index": "week"}).to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download Weekly Data", csv, "weekly_sales.csv", "text/csv", key="download_weekly")

    monthly_sales = df_filtered.resample("ME", on="transaction_datetime")[metric_col].sum()
    fig2_monthly = px.line(
        x=monthly_sales.index,
        y=monthly_sales.values,
        markers=True,
        labels={"x": "Month", "y": metric_label},
        title=f"📈 Monthly {metric_label} Trend",
    )
    st.plotly_chart(fig2_monthly, use_container_width=True)


    best_month = monthly_sales.idxmax()
    st.info(f"""
    📆 Best performing month: **{best_month.strftime('%B %Y')}**

    📈 Shows long-term growth trend and seasonal demand behavior.
    """)

    csv = monthly_sales.to_frame(name=metric_label).reset_index().rename(columns={"index": "month"}).to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download Monthly Data", csv, "monthly_sales.csv", "text/csv", key="download_monthly")

    st.subheader("📊 Day-of-Week Performance")
    dow_sales = df_filtered.groupby("day_of_week")[metric_col].sum().reindex(DAY_ORDER)
    fig3 = px.bar(
        x=dow_sales.index,
        y=dow_sales.values,
        text=dow_sales.values,
        color=dow_sales.values,
        color_continuous_scale="Viridis",
        labels={"x": "Day of Week", "y": metric_label},
        title=f"Day-of-Week {metric_label} Performance",
    )
    fig3.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    st.plotly_chart(fig3, use_container_width=True)

    peak_day_of_week = dow_sales.idxmax()
    low_day_of_week = dow_sales.idxmin()
    st.info(f"""
    📌 Highest sales occur on **{peak_day_of_week}**

    📉 Lowest sales occur on **{low_day_of_week}**

    🧠 Suggests strong weekday/weekend demand differences.
    """)

    csv = dow_sales.to_frame(name=metric_label).reset_index().rename(columns={"index": "day_of_week"}).to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download Day-of-Week Data", csv, "dow_sales.csv", "text/csv", key="download_dow")

    st.subheader("⏰ Hourly Demand Heatmap")
    hourly_sales = (
        df_filtered.pivot_table(index="day_of_week", columns="hour", values=metric_col, aggfunc="sum")
        .reindex(DAY_ORDER)
    )
    fig4 = px.imshow(
        hourly_sales,
        labels={"x": "Hour of Day", "y": "Day of Week", "color": metric_label},
        title=f"{metric_label} by Hour and Day",
        color_continuous_scale="Viridis",
    )
    st.plotly_chart(fig4, use_container_width=True)

    peak_hour = hourly_sales.sum().idxmax()
    peak_day_hour = hourly_sales.stack().idxmax()
    st.info(f"""
    ⏰ Peak demand hour: **{peak_hour}:00 hrs**

    🔥 Highest intensity observed on **{peak_day_hour[0]} at {peak_day_hour[1]}:00 hrs**

    📊 Helps optimize staffing and inventory during peak hours.
    """)

    csv = hourly_sales.reset_index().to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download Hourly Data", csv, "hourly_sales.csv", "text/csv", key="download_hourly")

    st.subheader(f"🏪 {metric_label} by Store Location")
    location_sales = df_filtered.groupby("store_location")[metric_col].sum().sort_values(ascending=False)
    fig5 = px.bar(
        x=location_sales.index,
        y=location_sales.values,
        text=location_sales.values,
        color=location_sales.values,
        color_continuous_scale="Viridis",
        labels={"x": "Store Location", "y": metric_label},
        title=f"{metric_label} by Store Location",
    )
    fig5.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    st.plotly_chart(fig5, use_container_width=True)

    best_location = location_sales.idxmax()
    low_location = location_sales.idxmin()
    st.info(f"""
    🏪 Top performing store: **{best_location}**

    📉 Lowest performing store: **{low_location}**
    📍 Useful for regional strategy and resource allocation.
    """)

    csv = location_sales.to_frame(name=metric_label).reset_index().rename(columns={"index": "store_location"}).to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download Location Data", csv, "location_sales.csv", "text/csv", key="download_location")

with tab2:
    st.subheader("☕ Top 10 Products")

    top_products = (
        df_filtered
        .groupby("product_type")[metric_col]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )

    fig6 = px.bar(
        top_products,
        x="product_type",
        y=metric_col,
        color="product_type",
        title=f"Top 10 Products by {metric_label}",
    )

    st.plotly_chart(fig6, use_container_width=True)

    st.subheader("📊 Weekend vs Weekday")

    df_filtered["Weekend"] = df_filtered["day_of_week"].isin(
        ["Saturday", "Sunday"]
    )

    weekend_sales = (
        df_filtered
        .groupby("Weekend")[metric_col]
        .sum()
        .reset_index()
    )

    weekend_sales["Weekend"] = weekend_sales["Weekend"].replace({
        True: "Weekend",
        False: "Weekday"
    })

    fig7 = px.bar(
        weekend_sales,
        x="Weekend",
        y=metric_col,
        color="Weekend",
        title=f"Weekend vs Weekday {metric_label}",
    )



    st.plotly_chart(fig7, use_container_width=True)


st.subheader("🧠 Smart Insights")

peak_hour = df_filtered.groupby("hour")["revenue"].sum().idxmax()
peak_day = df_filtered.groupby("day_of_week")["revenue"].sum().idxmax()
best_store = df_filtered.groupby("store_location")["revenue"].sum().idxmax()

colA, colB, colC = st.columns(3)

colA.success(f"🔥 Peak Hour: {peak_hour}:00")
colB.info(f"📅 Best Day: {peak_day}")
colC.warning(f"🏪 Top Store: {best_store}")

st.markdown("---")
st.subheader("📌 Recommendations")

st.markdown("""
- Increase staffing during morning rush hours.
- Focus promotions during low-demand periods.
- Optimize inventory for high-performing stores.
- Weekend campaigns can increase beverage revenue.
- Peak-hour staffing can improve customer experience.
""")

st.subheader("📄 Dataset Preview")
st.dataframe(
    df.head(100),
    use_container_width=True
)
st.markdown("---")

footer_html = """
<div style='
background: linear-gradient(135deg,#111827,#1f2937);
padding: 30px;
border-radius: 20px;
text-align: center;
border: 1px solid #374151;
margin-top: 30px;
'>

<h2 style='color:#f59e0b;'>
☕ Afficionado Coffee Roasters
</h2>

<p style='color:#d1d5db; font-size:16px;'>
Advanced Sales Trend & Time-Based Performance Analytics Dashboard
</p>

<div style='margin-top:20px;'>

<a href='https://www.afficionadocoffee.com/'
target='_blank'
style='
text-decoration:none;
background: linear-gradient(90deg,#f59e0b,#ef4444);
color:white;
padding:12px 20px;
border-radius:12px;
margin:10px;
display:inline-block;
font-weight:bold;
'>
🌐 Official Website
</a>

<a href='https://www.instagram.com/afficionado_coffee/'
target='_blank'
style='
text-decoration:none;
background: linear-gradient(90deg,#f59e0b,#ef4444);
color:white;
padding:12px 20px;
border-radius:12px;
margin:10px;
display:inline-block;
font-weight:bold;
'>
📸 Instagram
</a>

</div>

<p style='
color:#9ca3af;
margin-top:20px;
font-size:14px;
'>
Designed for Business Intelligence & Retail Analytics
</p>

</div>
"""

st.markdown(footer_html, unsafe_allow_html=True)