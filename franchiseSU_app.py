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

def calculate_scenario_revenues(base_revenue, scenario, growth_rate, years):
    """Calculate revenue projections for a given scenario"""
    if scenario == 'Weak Demand':
        start_pct = -15
    elif scenario == 'Above Average Demand':
        start_pct = 15
    else:  # Average Demand
        start_pct = 0
        
    starting_revenue = base_revenue * (1 + start_pct/100)
    return [starting_revenue * (1 + growth_rate/100) ** (year-1) for year in years]

def calculate_adjusted_margins(base_margin, years, cost_growth_rate):
    """Calculate margins accounting for compound cost growth effects"""
    adjusted_margins = []
    for year in years:
        # Compound effect of cost increases
        cost_multiplier = (1 + cost_growth_rate/100) ** (year-1)
        # Margin compression follows a more natural curve
        new_margin = base_margin / cost_multiplier
        adjusted_margins.append(new_margin)
    return adjusted_margins

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
    
    # Input controls in two rows of two columns
    col1, col2 = st.columns(2)
    with col1:
        selected_revenue = st.selectbox(
            'Select Revenue Scenario',
            ['Average Demand', 'Weak Demand', 'Above Average Demand'],
            key='revenue_scenario_select'
        )
    
    with col2:
        # Adjust default growth rate based on scenario
        if selected_revenue == 'Weak Demand':
            default_growth = 1.0
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
    
    col3, col4 = st.columns(2)
    with col3:
        cost_scenario = st.selectbox(
            'Select Cost Scenario',
            ['Average Costs', 'Below Average Costs', 'Above Average Costs'],
            key='cost_scenario_select_rev'
        )
    
    with col4:
        if cost_scenario == 'Below Average Costs':
            default_cost_growth = 2.0
        elif cost_scenario == 'Above Average Costs':
            default_cost_growth = 7.0
        else:
            default_cost_growth = 3.0
            
        cost_growth_rate = st.number_input(
            'Annual Cost Growth Rate (%)',
            min_value=-5.0,
            max_value=15.0,
            value=default_cost_growth,
            step=0.5,
            key='cost_growth_rate_rev'
        )

    # Calculate projections
    base_revenue = 530899
    years = range(1, 11)
    revenues = calculate_scenario_revenues(base_revenue, selected_revenue, growth_rate, years)
    base_margin = 0.2507
    adjusted_margins = calculate_adjusted_margins(base_margin, years, cost_growth_rate)
    profits = [rev * margin for rev, margin in zip(revenues, adjusted_margins)]

    # Display projection chart first
    st.header('Revenue and Profit Projections')
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=list(years),
        y=revenues,
        name='Revenue',
        line=dict(color='blue')
    ))
    
    fig.add_trace(go.Scatter(
        x=list(years),
        y=profits,
        name='Profit',
        line=dict(color='green')
    ))
    
    fig.update_layout(
        title=f"{selected_revenue} Scenario ({growth_rate:+.1f}% Growth)",
        xaxis_title="Year",
        yaxis_title="Amount ($)",
        template='plotly_white'
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # Scenario Impact Analysis with clear grouping and consistent metrics
    st.header('Scenario Impact Analysis')
    
    # Calculate all metrics first
    metrics = {
        'Year 1': {
            'revenue': revenues[0],
            'monthly_revenue': revenues[0] / 12,
            'profit': profits[0],
            'margin': profits[0] / revenues[0],
            'revenue_change': (revenues[0]/base_revenue - 1) * 100,
            'profit_change': (profits[0]/(base_revenue * base_margin) - 1) * 100
        },
        'Year 10': {
            'revenue': revenues[-1],
            'monthly_revenue': revenues[-1] / 12,
            'profit': profits[-1],
            'margin': profits[-1] / revenues[-1],
            'revenue_change': (revenues[-1]/revenues[0] - 1) * 100,
            'margin_change': (adjusted_margins[-1]/base_margin - 1) * 100
        },
        '10-Year Average': {
            'revenue': sum(revenues) / len(revenues),
            'monthly_revenue': sum(revenues) / len(revenues) / 12,
            'profit': sum(profits) / len(profits),
            'margin': sum(profits) / sum(revenues),
            'avg_annual_growth': ((revenues[-1]/revenues[0]) ** (1/9) - 1) * 100,
            'avg_margin_impact': (sum(adjusted_margins) / len(adjusted_margins) / base_margin - 1) * 100
        }
    }

    # Create three columns
    col1, col2, col3 = st.columns(3)
    
    # Display metrics in a consistent format
    columns = [col1, col2, col3]
    for col, (period, data) in zip(columns, metrics.items()):
        with col:
            st.subheader(period)
            
            # Annual Revenue (consistent across all periods)
            st.write("##### Annual Revenue")
            st.write(f"${data['revenue']:,.0f}")
            
            # Monthly Revenue (consistent across all periods)
            st.write("##### Monthly Revenue")
            st.write(f"${data['monthly_revenue']:,.0f}")
            
            # Profit (consistent across all periods)
            st.write("##### Profit")
            st.write(f"${data['profit']:,.0f}")
            
            # Margin (consistent across all periods)
            st.write("##### Margin")
            st.write(f"{(data['margin'] * 100):.1f}%")
            
            # Period-specific metrics
            st.write("##### Change Metrics")
            if period == 'Year 1':
                st.write(f"Revenue vs Baseline: {data['revenue_change']:+.1f}%")
                st.write(f"Profit vs Baseline: {data['profit_change']:+.1f}%")
            elif period == 'Year 10':
                st.write(f"Total Revenue Growth: {data['revenue_change']:+.1f}%")
                st.write(f"Total Margin Impact: {data['margin_change']:+.1f}%")
            else:  # 10-Year Average
                st.write(f"Avg Annual Growth: {data['avg_annual_growth']:+.1f}%")
                st.write(f"Avg Margin Impact: {data['avg_margin_impact']:+.1f}%")

    # Move baseline metrics to the bottom
    st.header('Baseline Performance (July 2023 - June 2024)')
    
    col4, col5 = st.columns(2)
    
    with col4:
        st.subheader('Revenue Metrics')
        baseline_metrics = calculate_financials(base_revenue)
        st.write(f"Gross Revenue: ${base_revenue:,.2f}")
        st.write(f"Gross Profit: ${baseline_metrics['gross_profit']:,.2f}")
    
    with col5:
        st.subheader('Cost Metrics')
        for key, value in baseline_metrics.items():
            if key not in ['revenue', 'gross_profit']:
                st.write(f"{key.replace('_', ' ').title()}: ${value:,.2f} ({value/base_revenue*100:.2f}%)")

def calculate_sensitivity_npv(base_params, param_name, variation_pct):
    """Calculate NPV for parameter variations"""
    params = base_params.copy()
    
    # Adjust the specified parameter up and down by variation_pct
    if param_name == 'initial_investment':
        params[param_name] = base_params[param_name] * (1 + variation_pct/100)
    elif param_name == 'growth_rate':
        params[param_name] = base_params[param_name] + variation_pct
    elif param_name == 'discount_rate':
        params[param_name] = base_params[param_name] + variation_pct
    elif param_name == 'cost_growth':
        params[param_name] = base_params[param_name] + variation_pct
    
    # Recalculate cash flows with new parameters
    years = range(1, 11)
    revenues = [params['base_revenue'] * (1 + params['growth_rate']/100) ** (year-1) for year in years]
    adjusted_margins = [0.2507 * (1 - (params['cost_growth']/100) * year) for year in years]
    cash_flows = [rev * margin for rev, margin in zip(revenues, adjusted_margins)]
    
    # Calculate NPV with new cash flows
    full_cash_flows = [-params['initial_investment']] + cash_flows
    return npf.npv(params['discount_rate']/100, full_cash_flows)

def create_tornado_plot(base_params):
    """Create tornado plot showing NPV sensitivity"""
    # Parameters to vary and their ranges
    parameters = {
        'initial_investment': {'variation': 20, 'label': 'Initial Investment (±20%)'},
        'growth_rate': {'variation': 2, 'label': 'Growth Rate (±2%)'},
        'discount_rate': {'variation': 2, 'label': 'Discount Rate (±2%)'},
        'cost_growth': {'variation': 2, 'label': 'Cost Growth Rate (±2%)'}
    }
    
    # Calculate base NPV
    base_npv = calculate_sensitivity_npv(base_params, 'initial_investment', 0)
    
    # Calculate NPV changes for each parameter
    sensitivity_results = []
    
    for param, details in parameters.items():
        # Calculate NPV for parameter increase and decrease
        npv_increase = calculate_sensitivity_npv(base_params, param, details['variation'])
        npv_decrease = calculate_sensitivity_npv(base_params, param, -details['variation'])
        
        # Store results
        sensitivity_results.append({
            'parameter': details['label'],
            'npv_change_low': npv_decrease - base_npv,
            'npv_change_high': npv_increase - base_npv
        })
    
    # Sort results by absolute impact
    sensitivity_results.sort(key=lambda x: max(abs(x['npv_change_low']), abs(x['npv_change_high'])))
    
    # Create tornado plot
    fig = go.Figure()
    
    # Add bars for each parameter
    for result in sensitivity_results:
        fig.add_trace(go.Bar(
            y=[result['parameter']],
            x=[result['npv_change_high']],
            orientation='h',
            name='Increase',
            marker_color='rgba(55, 128, 191, 0.7)',
            showlegend=False
        ))
        
        fig.add_trace(go.Bar(
            y=[result['parameter']],
            x=[result['npv_change_low']],
            orientation='h',
            name='Decrease',
            marker_color='rgba(219, 64, 82, 0.7)',
            showlegend=False
        ))
    
    fig.update_layout(
        title='NPV Sensitivity Analysis',
        xaxis_title='Change in NPV ($)',
        yaxis_title='Parameter',
        barmode='overlay',
        bargap=0.1,
        template='plotly_white',
        height=400
    )
    
    return fig

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
    def calculate_adjusted_margins(base_margin, years, cost_growth_rate):
        """Calculate margins accounting for compound cost growth effects"""
        adjusted_margins = []
        for year in years:
            # Compound effect of cost increases
            cost_multiplier = (1 + cost_growth_rate/100) ** (year-1)
            # Margin compression follows a more natural curve
            new_margin = base_margin / cost_multiplier
            adjusted_margins.append(new_margin)
        return adjusted_margins

    # Calculate cash flows with cost adjustments
    initial_investment = startup_costs[selected_cost]
    starting_revenue = base_revenue * (1 + start_pct/100)
    
    years = range(1, 11)
    revenues = [starting_revenue * (1 + growth_rate/100) ** (year-1) for year in years]
    
    # Adjust profit margins for each year based on cost growth
    base_margin = 0.2507  # Initial gross profit margin
    adjusted_margins = calculate_adjusted_margins(base_margin, years, cost_growth_rate)
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
    
    # Margin Analysis
    st.header('Margin Analysis')
    
    # Add explanation before the chart
    st.write("""
    The Gross Margin Projection chart shows how your profit margins may evolve over time:
    - **Blue Line**: Shows the projected gross margin after accounting for cost increases
    - **Gray Dashed Line**: Shows the baseline gross margin of 25.07% for comparison
    - The gap between the lines represents margin erosion due to rising costs
    - Steeper decline indicates more significant impact from cost growth
    - This analysis helps identify when cost management or price adjustments may be needed
    """)
    
    # Margin analysis chart
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
    
    st.plotly_chart(fig_margins, use_container_width=True)
    
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
    
    # Add tornado plot after the waterfall chart
    st.header('Sensitivity Analysis')
    
    # Create base parameters dictionary
    base_params = {
        'initial_investment': initial_investment,
        'base_revenue': starting_revenue,
        'growth_rate': growth_rate,
        'discount_rate': discount_rate,
        'cost_growth': cost_growth_rate
    }
    
    # Create and display tornado plot
    tornado_fig = create_tornado_plot(base_params)
    st.plotly_chart(tornado_fig, use_container_width=True)
    
    # Add explanation
    st.write("""
    This tornado plot shows how changes in key input parameters affect the NPV:
    - Bars extending to the right (blue) show the impact of increasing the parameter
    - Bars extending to the left (red) show the impact of decreasing the parameter
    - Longer bars indicate higher sensitivity to that parameter
    - Parameters are sorted by their impact magnitude
    """)
    
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
    
    # Store current values in session state
    st.session_state.current_npv = npv
    st.session_state.current_irr = irr
    st.session_state.current_payback = payback
    st.session_state.current_revenues = revenues
    st.session_state.current_profits = profits
    st.session_state.current_margins = adjusted_margins
    st.session_state.current_investment = initial_investment
    st.session_state.current_cost_growth = cost_growth_rate
    st.session_state.current_growth_rate = growth_rate
    st.session_state.current_revenue_scenario = selected_revenue
    st.session_state.current_cost_scenario = cost_scenario

def generate_investment_report(npv, irr, payback, initial_investment, revenues, profits, adjusted_margins, 
                             cost_growth_rate, growth_rate, selected_revenue, cost_scenario):
    """Generate a comprehensive investment analysis report"""
    
    # Investment Overview
    overview = f"""
    ## Investment Overview
    Based on the selected scenario analysis ({selected_revenue} with {cost_scenario}), 
    this franchise opportunity requires an initial investment of ${initial_investment:,.0f} and shows the following key metrics:
    
    * Net Present Value (NPV): ${npv:,.0f}
    * Internal Rate of Return (IRR): {irr:.1f}%
    * Payback Period: {payback:.1f} years
    """
    
    # Financial Performance
    year_10_revenue = revenues[-1]
    year_10_profit = profits[-1]
    avg_revenue = sum(revenues) / len(revenues)
    avg_profit = sum(profits) / len(profits)
    final_margin = adjusted_margins[-1]
    
    performance = f"""
    ## Financial Performance
    The business is projected to grow from ${revenues[0]:,.0f} in Year 1 to ${year_10_revenue:,.0f} in Year 10, 
    with an annual growth rate of {growth_rate:.1f}%. The average annual revenue over the 10-year period is ${avg_revenue:,.0f}.
    
    Profitability metrics show:
    * Average annual profit: ${avg_profit:,.0f}
    * Final year profit: ${year_10_profit:,.0f}
    * Ending gross margin: {final_margin*100:.1f}%
    """
    
    # Risk Assessment
    risk_level = "LOW" if irr > 25 else "MODERATE" if irr > 15 else "HIGH"
    margin_decline = ((adjusted_margins[-1] / adjusted_margins[0]) - 1) * 100
    
    risks = f"""
    ## Risk Assessment
    The overall investment risk is assessed as **{risk_level}** based on:
    
    * Cost Pressure: {cost_growth_rate:.1f}% annual increase, leading to a {abs(margin_decline):.1f}% margin decline over 10 years
    * Market Risk: Captured in the {selected_revenue} scenario
    * Operational Risk: Reflected in {cost_scenario} scenario
    """
    
    # Investment Recommendation
    if npv > 0 and irr > 15 and payback < 7:
        recommendation = "RECOMMENDED"
        rationale = f"""
        This investment opportunity appears **favorable** based on:
        * Positive NPV of ${npv:,.0f}
        * Strong IRR of {irr:.1f}%
        * Reasonable payback period of {payback:.1f} years
        """
    elif npv > 0 and irr > 10:
        recommendation = "CAUTIOUSLY POSITIVE"
        rationale = f"""
        This investment opportunity appears **viable but requires careful consideration** based on:
        * Positive but moderate NPV of ${npv:,.0f}
        * Acceptable IRR of {irr:.1f}%
        * Extended payback period of {payback:.1f} years
        """
    else:
        recommendation = "NOT RECOMMENDED"
        rationale = f"""
        This investment opportunity appears **challenging** based on:
        * Limited NPV of ${npv:,.0f}
        * Below-target IRR of {irr:.1f}%
        * Long payback period of {payback:.1f} years
        """
    
    conclusion = f"""
    ## Investment Recommendation: {recommendation}
    
    {rationale}
    
    ### Key Success Factors
    To maximize the chance of success, focus on:
    1. Cost management to maintain margins above {adjusted_margins[-1]*100:.1f}%
    2. Revenue growth initiatives to achieve or exceed {growth_rate:.1f}% annual growth
    3. Operational efficiency to combat the projected {cost_growth_rate:.1f}% annual cost increases
    """
    
    return overview + performance + risks + conclusion

def investment_report_tab():
    st.title('Investment Analysis Report')
    
    # Get current values from session state or recalculate
    if 'current_npv' in st.session_state:
        npv = st.session_state.current_npv
        irr = st.session_state.current_irr
        payback = st.session_state.current_payback
        revenues = st.session_state.current_revenues
        profits = st.session_state.current_profits
        adjusted_margins = st.session_state.current_margins
        initial_investment = st.session_state.current_investment
        cost_growth_rate = st.session_state.current_cost_growth
        growth_rate = st.session_state.current_growth_rate
        selected_revenue = st.session_state.current_revenue_scenario
        cost_scenario = st.session_state.current_cost_scenario
        
        # Generate and display report
        report = generate_investment_report(
            npv, irr, payback, initial_investment, revenues, profits, 
            adjusted_margins, cost_growth_rate, growth_rate, 
            selected_revenue, cost_scenario
        )
        
        st.markdown(report)
        
        # Add download button for report
        report_download = report.replace('##', '#').replace('*', '-')
        st.download_button(
            label="Download Report",
            data=report_download,
            file_name="franchise_investment_analysis.md",
            mime="text/markdown"
        )
    else:
        st.warning("Please complete the financial analysis first to generate the investment report.")

def main():
    tab1, tab2, tab3, tab4 = st.tabs([
        "Startup Costs", 
        "Revenue Projections", 
        "Financial Analysis",
        "Investment Report"
    ])
    
    with tab1:
        startup_costs_tab()
    with tab2:
        revenue_projections_tab()
    with tab3:
        financial_analysis_tab()
    with tab4:
        investment_report_tab()

if __name__ == '__main__':
    main()
