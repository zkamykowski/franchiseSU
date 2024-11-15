import streamlit as st
import plotly.graph_objects as go
import numpy as np
import numpy_financial as npf

def calculate_financials(revenue):
    """Calculate all financial metrics based on baseline percentages"""
    return {
        'revenue': revenue,
        'cogs': revenue * 0.2443,  # Cost of Goods Sold: 24.43%
        'labor': revenue * 0.3138,  # Labor Cost: 31.38%
        'occupancy': revenue * 0.1150,  # Occupancy Cost: 11.50%
        'operating': revenue * 0.0095,  # Operating Expenses: 0.95%
        'royalties': revenue * 0.0400,  # Royalties: 4.00%
        'franchise_expense': revenue * 0.0268,  # Franchise-Related: 2.68%
        'gross_profit': revenue * 0.2507  # Gross Profit: 25.07%
    }

def calculate_npv_metrics(initial_investment, cash_flows, discount_rate):
    """Calculate NPV, IRR, and payback period"""
    # Add initial investment as first cash flow (negative)
    full_cash_flows = [-initial_investment] + cash_flows
    
    # NPV calculation
    npv = npf.npv(discount_rate/100, full_cash_flows)
    
    # IRR calculation
    try:
        irr = npf.irr(full_cash_flows) * 100
    except:
        irr = None
    
    # Payback period calculation
    cumulative = np.cumsum(full_cash_flows)
    payback = np.where(cumulative >= 0)[0]
    if len(payback) > 0:
        payback_period = payback[0]
        # Interpolate for more accurate payback period
        if payback_period > 0:
            prev_cum = cumulative[payback_period-1]
            curr_cum = cumulative[payback_period]
            payback_period = payback_period - 1 + abs(prev_cum) / (curr_cum - prev_cum)
    else:
        payback_period = None
    
    return npv, irr, payback_period

def startup_costs_tab():
    st.title('Startup Costs Analysis')
    
    # Create startup costs dictionary
    startup_costs = {
        'Initial Franchise Fee': {'low': 35000, 'high': 35000},
        'Computer System': {'low': 5000, 'high': 8000},
        'Insurance': {'low': 5000, 'high': 7000},
        'Professional Fees': {'low': 5000, 'high': 7500},
        'Travel, Lodging, and Meals': {'low': 2000, 'high': 8000},
        'Equipment': {'low': 100000, 'high': 160000},
        'Construction and Leasehold Improvements': {'low': 200000, 'high': 460000},
        'Signage': {'low': 6000, 'high': 20000},
        'Permits and Licenses': {'low': 500, 'high': 5000},
        'Project Management & Architect Fees': {'low': 10000, 'high': 35000},
        'Office Equipment and Supplies': {'low': 500, 'high': 1000},
        'Initial Inventory': {'low': 8000, 'high': 12000},
        'Utilities Lease and Security Deposits': {'low': 4500, 'high': 30000},
        'Grand Opening and Initial Advertising': {'low': 5000, 'high': 10000},
        'Pre-opening Employee Wages': {'low': 1000, 'high': 5000},
        'Additional Funds (3 Months)': {'low': 40000, 'high': 80000}
    }
    
    # Scenario Selection
    cost_scenario = st.selectbox(
        'Select Cost Scenario',
        ['Average Cost', 'Low Cost', 'High Cost']
    )
    
    # Calculate costs based on scenario
    if cost_scenario == 'Low Cost':
        multiplier = 1.0
        base_costs = {k: v['low'] for k, v in startup_costs.items()}
    elif cost_scenario == 'High Cost':
        multiplier = 1.0
        base_costs = {k: v['high'] for k, v in startup_costs.items()}
    else:  # Average Cost
        multiplier = 1.0
        base_costs = {k: (v['low'] + v['high'])/2 for k, v in startup_costs.items()}
    
    # Display costs breakdown
    st.header('Startup Costs Breakdown')
    
    total_cost = 0
    for category, amount in base_costs.items():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**{category}**")
        with col2:
            st.write(f"${amount * multiplier:,.2f}")
        total_cost += amount * multiplier
    
    st.markdown("---")
    st.header('Total Investment Required')
    st.write(f"**Total Cost: ${total_cost:,.2f}**")
    
    # Add comparison visualization
    st.header('Cost Comparison')
    fig = go.Figure()
    
    # Add bars for all scenarios
    scenarios = {
        'Low Cost': sum(v['low'] for v in startup_costs.values()),
        'Average Cost': sum((v['low'] + v['high'])/2 for v in startup_costs.values()),
        'High Cost': sum(v['high'] for v in startup_costs.values())
    }
    
    colors = {'Low Cost': 'green', 'Average Cost': 'blue', 'High Cost': 'red'}
    
    for scenario, amount in scenarios.items():
        fig.add_trace(
            go.Bar(
                name=scenario,
                x=[scenario],
                y=[amount],
                marker_color=colors[scenario],
                width=0.4,
                opacity=1 if scenario == cost_scenario else 0.7
            )
        )
    
    fig.update_layout(
        title="Investment Requirements by Scenario",
        yaxis_title="Total Investment ($)",
        showlegend=False,
        template='plotly_white'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def revenue_projections_tab():
    st.title('Revenue Projections Analysis')
    
    # Cost scenario selection
    col1, col2 = st.columns(2)
    with col1:
        cost_scenario = st.selectbox(
            'Select Cost Scenario',
            ['Average Costs', 'Below Average Costs', 'Above Average Costs'],
            key='cost_scenario_select_rev'
        )
    
    # Cost growth rate input based on scenario
    with col2:
        if cost_scenario == 'Below Average Costs':
            default_cost_growth = 2.0
            cost_growth_rate = st.number_input(
                'Annual Cost Growth Rate (%)',
                min_value=-5.0,
                max_value=10.0,
                value=default_cost_growth,
                step=0.5,
                help="Default is 2% for Below Average scenario",
                key='below_avg_cost_growth_rev'
            )
        elif cost_scenario == 'Above Average Costs':
            default_cost_growth = 7.0
            cost_growth_rate = st.number_input(
                'Annual Cost Growth Rate (%)',
                min_value=-5.0,
                max_value=15.0,
                value=default_cost_growth,
                step=0.5,
                help="Default is 7% for Above Average scenario",
                key='above_avg_cost_growth_rev'
            )
        else:  # Average Costs
            default_cost_growth = 3.0
            cost_growth_rate = st.number_input(
                'Annual Cost Growth Rate (%)',
                min_value=-5.0,
                max_value=12.0,
                value=default_cost_growth,
                step=0.5,
                help="Default is 3% for Average scenario",
                key='avg_cost_growth_rev'
            )

    # Revenue scenario selection
    col3, col4 = st.columns(2)
    with col3:
        selected_revenue = st.selectbox(
            'Select Revenue Scenario',
            ['Average Demand', 'Weak Demand', 'Above Average Demand'],
            key='revenue_scenario_select'
        )
    
    with col4:
        # Adjust default growth rate based on scenario
        if selected_revenue == 'Weak Demand':
            default_growth = 1.0  # Changed from 0 to 1%
        elif selected_revenue == 'Above Average Demand':
            default_growth = 10.0
        else:
            default_growth = 5.0
            
        growth_rate = st.slider(
            'Annual Growth Rate (%)',
            min_value=-2.0,
            max_value=15.0,
            value=default_growth,
            step=0.5
        )

    # Calculate baseline metrics with cost adjustments
    base_revenue = 530899
    baseline_metrics = calculate_financials(base_revenue)
    
    # Display baseline metrics
    st.header('Baseline Performance (July 2023 - June 2024)')
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Revenue Metrics**")
        st.write(f"Gross Revenue: ${baseline_metrics['revenue']:,.2f}")
        st.write(f"Gross Profit: ${baseline_metrics['gross_profit']:,.2f}")
    
    with col2:
        st.write("**Cost Metrics**")
        st.write(f"Cost of Goods Sold: ${baseline_metrics['cogs']:,.2f} (24.43%)")
        st.write(f"Labor Cost: ${baseline_metrics['labor']:,.2f} (31.38%)")
        st.write(f"Occupancy Cost: ${baseline_metrics['occupancy']:,.2f} (11.50%)")
        st.write(f"Operating Expenses: ${baseline_metrics['operating']:,.2f} (0.95%)")
        st.write(f"Royalties: ${baseline_metrics['royalties']:,.2f} (4.00%)")
        st.write(f"Franchise-Related: ${baseline_metrics['franchise_expense']:,.2f} (2.68%)")
    
    st.markdown("---")
    
    # Update scenario impact analysis to include cost effects
    def calculate_adjusted_margins(base_margin, year, cost_growth_rate):
        cost_multiplier = (1 + cost_growth_rate/100) ** year
        return base_margin - (base_margin * (cost_multiplier - 1))

    # Calculate projections with both revenue growth and cost effects
    years = range(1, 11)
    base_margin = 0.2507  # Initial gross profit margin
    
    if selected_revenue == 'Weak Demand':
        start_pct = -15
    elif selected_revenue == 'Above Average Demand':
        start_pct = 15
    else:
        start_pct = 0
        
    starting_revenue = base_revenue * (1 + start_pct/100)
    revenues = [starting_revenue * (1 + growth_rate/100) ** (year-1) for year in years]
    adjusted_margins = [calculate_adjusted_margins(base_margin, year, cost_growth_rate) for year in years]
    profits = [rev * margin for rev, margin in zip(revenues, adjusted_margins)]

    # Update scenario impact analysis display
    st.header('Scenario Impact Analysis')
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader('Year 1')
        st.write(f"Revenue: ${revenues[0]:,.0f}")
        st.write(f"Profit: ${profits[0]:,.0f}")
        st.write(f"Revenue Change: {((revenues[0]/base_revenue - 1) * 100):+.1f}%")
        st.write(f"Profit Change: {((profits[0]/baseline_metrics['gross_profit'] - 1) * 100):+.1f}%")
        
    with col2:
        st.subheader('Year 10')
        st.write(f"Revenue: ${revenues[-1]:,.0f}")
        st.write(f"Profit: ${profits[-1]:,.0f}")
        st.write(f"Total Growth: {((revenues[-1]/revenues[0] - 1) * 100):+.1f}%")
        st.write(f"Margin Impact: {((adjusted_margins[-1]/base_margin - 1) * 100):+.1f}%")

    # Add average metrics
    st.subheader('10-Year Average')
    avg_revenue = sum(revenues) / len(revenues)
    avg_profit = sum(profits) / len(profits)
    st.write(f"Revenue: ${avg_revenue:,.0f}")
    st.write(f"Profit: ${avg_profit:,.0f}")
    st.write(f"Monthly Revenue: ${avg_revenue/12:,.0f}")
    st.write(f"Monthly Profit: ${avg_profit/12:,.0f}")
    
    # Revenue Projection Chart
    st.markdown("---")
    st.header('Revenue Projection Chart')
    
    # Create visualization with unique key
    fig = go.Figure()
    years = list(range(1, 11))
    
    # Define scenarios
    scenarios = {
        'Weak Demand': {'growth_rate': -2.0, 'color': 'red'},
        'Average Demand': {'growth_rate': 5.0, 'color': 'blue'},
        'Above Average Demand': {'growth_rate': 10.0, 'color': 'green'}
    }
    
    # Add lines for all scenarios
    for scenario in scenarios:
        if scenario == selected_revenue:
            scenario_growth = growth_rate
        else:
            scenario_growth = scenarios[scenario]['growth_rate']
        
        revenues = calculate_scenario_revenues(
            base_revenue, 
            scenario, 
            scenario_growth, 
            weak_pct, 
            above_pct
        )
        
        fig.add_trace(
            go.Scatter(
                x=years,
                y=revenues,
                name=scenario,
                line=dict(
                    color=scenarios[scenario]['color'],
                    width=3 if scenario == selected_revenue else 1.5,
                    dash='solid' if scenario == selected_revenue else 'dot'
                )
            )
        )
    
    fig.update_layout(
        title="Revenue Projections Comparison",
        xaxis_title="Year",
        yaxis_title="Revenue ($)",
        template='plotly_white',
        hovermode='x unified'
    )
    
    # Add unique key to plotly chart
    st.plotly_chart(fig, use_container_width=True, key="revenue_projection_chart")

def financial_analysis_tab():
    st.title('Financial Analysis')
    
    # Define startup costs dictionary
    startup_costs = {
        'Low Cost': 417500,
        'Average Cost': 650500,
        'High Cost': 883500
    }
    
    # Cost scenario selection
    col1, col2 = st.columns(2)
    with col1:
        cost_scenario = st.selectbox(
            'Select Cost Scenario',
            ['Average Costs', 'Below Average Costs', 'Above Average Costs'],
            key='cost_scenario_select'
        )
    
    # Investment scenario selection
    selected_cost = st.selectbox(
        'Select Investment Level',
        ['Low Cost', 'Average Cost', 'High Cost'],
        key='investment_select'
    )
    
    # Cost growth rate input based on scenario
    with col2:
        if cost_scenario == 'Below Average Costs':
            default_cost_growth = 2.0
            cost_growth_rate = st.number_input(
                'Annual Cost Growth Rate (%)',
                min_value=-5.0,
                max_value=10.0,
                value=default_cost_growth,
                step=0.5,
                help="Default is 2% for Below Average scenario",
                key='below_avg_cost_growth'
            )
        elif cost_scenario == 'Above Average Costs':
            default_cost_growth = 7.0
            cost_growth_rate = st.number_input(
                'Annual Cost Growth Rate (%)',
                min_value=-5.0,
                max_value=15.0,
                value=default_cost_growth,
                step=0.5,
                help="Default is 7% for Above Average scenario",
                key='above_avg_cost_growth'
            )
        else:  # Average Costs
            default_cost_growth = 3.0
            cost_growth_rate = st.number_input(
                'Annual Cost Growth Rate (%)',
                min_value=-5.0,
                max_value=12.0,
                value=default_cost_growth,
                step=0.5,
                help="Default is 3% for Average scenario",
                key='avg_cost_growth'
            )

    # Revenue scenario selection
    col3, col4 = st.columns(2)
    with col3:
        selected_revenue = st.selectbox(
            'Select Revenue Scenario',
            ['Average Demand', 'Weak Demand', 'Above Average Demand'],
            key='revenue_scenario_select_financial'
        )
    
    with col4:
        discount_rate = st.slider(
            'Discount Rate (%)',
            min_value=8.0,
            max_value=20.0,
            value=13.0,
            step=0.5,
            help="Industry standard for small franchise operations typically ranges from 12-15%",
            key='discount_rate_slider'
        )

    # Define base revenue and scenario parameters
    base_revenue = 530899
    if selected_revenue == 'Weak Demand':
        start_pct = -15
        growth_rate = 0
    elif selected_revenue == 'Above Average Demand':
        start_pct = 15
        growth_rate = 10
    else:
        start_pct = 0
        growth_rate = 5

    # Calculate adjusted margins based on cost growth
    def calculate_adjusted_margins(base_margin, year, cost_growth_rate):
        cost_multiplier = (1 + cost_growth_rate/100) ** year
        # Adjust the margin inversely to cost growth
        return base_margin - (base_margin * (cost_multiplier - 1))

    # Calculate cash flows with cost adjustments
    initial_investment = startup_costs[selected_cost]
    starting_revenue = base_revenue * (1 + start_pct/100)
    
    years = range(1, 11)
    revenues = [starting_revenue * (1 + growth_rate/100) ** (year-1) for year in years]
    
    # Adjust profit margins for each year based on cost growth
    base_margin = 0.2507  # Initial gross profit margin
    adjusted_margins = [calculate_adjusted_margins(base_margin, year, cost_growth_rate) for year in years]
    cash_flows = [rev * margin for rev, margin in zip(revenues, adjusted_margins)]
    
    # Calculate metrics with adjusted cash flows
    npv, irr, payback = calculate_npv_metrics(initial_investment, cash_flows, discount_rate)
    
    # Display metrics
    st.header('Investment Metrics')
    col1, col2, col3 = st.columns(3)
    
    with col1:
        npv_formatted = "${:,.0f}".format(npv) if npv is not None else "N/A"
        st.metric(
            label="Net Present Value",
            value=npv_formatted,
            delta=None
        )
    with col2:
        irr_formatted = "{:.1f}%".format(irr) if irr is not None else "N/A"
        st.metric(
            label="Internal Rate of Return",
            value=irr_formatted,
            delta=None
        )
    with col3:
        payback_formatted = "{:.1f} years".format(payback) if payback is not None else "N/A"
        st.metric(
            label="Payback Period",
            value=payback_formatted,
            delta=None
        )
    
    # Add margin analysis chart
    st.header('Margin Analysis')
    fig_margins = go.Figure()
    
    fig_margins.add_trace(go.Scatter(
        x=list(years),
        y=[margin * 100 for margin in adjusted_margins],
        name='Adjusted Gross Margin',
        line=dict(color='blue')
    ))
    
    fig_margins.add_trace(go.Scatter(
        x=list(years),
        y=[base_margin * 100] * len(years),
        name='Base Gross Margin',
        line=dict(color='gray', dash='dash')
    ))
    
    fig_margins.update_layout(
        title="Gross Margin Projection",
        xaxis_title="Year",
        yaxis_title="Gross Margin (%)",
        template='plotly_white'
    )
    
    st.plotly_chart(fig_margins, use_container_width=True, key="margin_analysis_chart")
    
    # Update waterfall chart to show cost impact
    fig_waterfall = go.Figure()
    
    fig_waterfall.add_trace(go.Waterfall(
        name="Cash Flow",
        orientation="v",
        measure=["relative"] + ["relative"] * 10,
        x=["Initial"] + [f"Year {year}" for year in years],
        y=[-initial_investment] + cash_flows,
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        decreasing={"marker": {"color": "red"}},
        increasing={"marker": {"color": "green"}},
        totals={"marker": {"color": "blue"}}
    ))
    
    fig_waterfall.update_layout(
        title="Cash Flow Waterfall (Including Cost Effects)",
        showlegend=False,
        xaxis_title="Period",
        yaxis_title="Cash Flow ($)",
        template='plotly_white'
    )
    
    st.plotly_chart(fig_waterfall, use_container_width=True, key="waterfall_chart")
    
    # Update risk assessment
    st.header('Risk Assessment')
    st.write(f"""
    **Key Risk Factors:**
    1. Initial Investment Risk: Selected scenario assumes **${startup_costs[selected_cost]:,.0f}** investment level
    2. Revenue Risk: **{selected_revenue}** scenario with **{growth_rate:.1f}%** annual growth
    3. Cost Risk: **{cost_scenario}** with **{cost_growth_rate:.1f}%** annual growth
    4. Margin Risk: Starting margin of **25.07%** declining to **{(adjusted_margins[-1]*100):.2f}%** by Year 10
    5. Market Risk: Captured in **{discount_rate:.1f}%** discount rate
    
    **Break-even Analysis:**
    - Time to break-even: **{payback:.1f}** years
    - Required monthly revenue at break-even: **${(starting_revenue/12):,.0f}**
    
    **Investment Summary:**
    - Initial Investment: **${initial_investment:,.0f}**
    - Year 1 Revenue: **${revenues[0]:,.0f}**
    - Year 1 Cash Flow: **${cash_flows[0]:,.0f}**
    - Year 10 Cash Flow: **${cash_flows[-1]:,.0f}**
    - 10-Year NPV: **${npv:,.0f}**
    """)

def main():
    tab1, tab2, tab3 = st.tabs(["Startup Costs", "Revenue Projections", "Financial Analysis"])
    
    with tab1:
        startup_costs_tab()
    with tab2:
        revenue_projections_tab()
    with tab3:
        financial_analysis_tab()

if __name__ == '__main__':
    main()
