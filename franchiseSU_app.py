import streamlit as st
import plotly.graph_objects as go
import numpy as np
import numpy_financial as npf
import fpdf
from fpdf import FPDF
import tempfile

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
    
    # Create startup costs dictionary with default values
    default_startup_costs = {
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
    
    # Calculate scenario totals for use in other tabs
    st.session_state.startup_costs = {
        'Low Cost': sum(v['low'] for v in default_startup_costs.values()),
        'Average Cost': sum((v['low'] + v['high'])/2 for v in default_startup_costs.values()),
        'High Cost': sum(v['high'] for v in default_startup_costs.values())
    }
    
    # Scenario Selection
    cost_scenario = st.selectbox(
        'Select Cost Scenario',
        ['Average Cost', 'Low Cost', 'High Cost'],
        key='cost_scenario_startup'
    )
    
    # Initialize or reset session state for current costs when scenario changes
    if 'current_costs' not in st.session_state or st.session_state.get('last_scenario') != cost_scenario:
        if cost_scenario == 'Low Cost':
            st.session_state.current_costs = {k: v['low'] for k, v in default_startup_costs.items()}
        elif cost_scenario == 'High Cost':
            st.session_state.current_costs = {k: v['high'] for k, v in default_startup_costs.items()}
        else:  # Average Cost
            st.session_state.current_costs = {k: (v['low'] + v['high'])/2 for k, v in default_startup_costs.items()}
        st.session_state.last_scenario = cost_scenario
    
    # Display costs breakdown with adjustable inputs
    st.header('Startup Costs Breakdown')
    
    total_cost = 0
    for category in default_startup_costs.keys():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**{category}**")
        with col2:
            # Get min and max values for this category
            min_val = default_startup_costs[category]['low']
            max_val = default_startup_costs[category]['high']
            
            # Create number input with appropriate step size
            step = 100.0 if max_val > 10000 else 50.0
            current_value = st.number_input(
                f"Amount for {category}",
                min_value=min_val * 0.5,  # Allow going 50% below minimum
                max_value=max_val * 1.5,  # Allow going 50% above maximum
                value=st.session_state.current_costs[category],
                step=step,
                key=f"input_{category}",
                label_visibility="collapsed"
            )
            st.session_state.current_costs[category] = current_value
            total_cost += current_value
    
    st.markdown("---")
    st.header('Total Investment Required')
    st.write(f"**Total Cost: ${total_cost:,.2f}**")
    
    # Add comparison visualization
    st.header('Cost Comparison')
    fig = go.Figure()
    
    # Calculate scenario totals
    scenarios = {
        'Low Cost': sum(v['low'] for v in default_startup_costs.values()),
        'Average Cost': sum((v['low'] + v['high'])/2 for v in default_startup_costs.values()),
        'High Cost': sum(v['high'] for v in default_startup_costs.values())
    }
    
    # Add current total to scenarios
    scenarios['Current Selection'] = total_cost
    
    colors = {
        'Low Cost': 'green',
        'Average Cost': 'blue',
        'High Cost': 'red',
        'Current Selection': 'purple'
    }
    
    for scenario, amount in scenarios.items():
        fig.add_trace(
            go.Bar(
                name=scenario,
                x=[scenario],
                y=[amount],
                marker_color=colors[scenario],
                width=0.4,
                opacity=1 if scenario == 'Current Selection' else 0.7
            )
        )
    
    fig.update_layout(
        title="Investment Requirements Comparison",
        yaxis_title="Total Investment ($)",
        showlegend=False,
        template='plotly_white'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Store the current total in session state for other tabs
    st.session_state.current_total_investment = total_cost

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
        'cost_growth': {'variation': 2, 'label': 'Cost Growth Rate (2%)'}
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
    
    # Initial Investment Section
    st.header('Initial Investment')
    selected_cost = st.selectbox(
        'Select Investment Level',
        ['Average Cost', 'Low Cost', 'High Cost'],
        index=0,  # Default to Average Cost
        key='startup_cost_select'
    )
    
    # Get investment amount from session state
    if 'startup_costs' not in st.session_state:
        st.error("Please visit the Startup Costs tab first to initialize investment amounts.")
        st.stop()
    
    initial_investment = st.session_state.startup_costs[selected_cost]
    st.write(f"Initial Investment: **${initial_investment:,.0f}**")
    
    # Business Scenario Section
    st.header('Business Scenario Analysis')
    
    # Revenue controls
    col1, col2 = st.columns(2)
    with col1:
        selected_revenue = st.selectbox(
            'Select Revenue Scenario',
            ['Average Demand', 'Weak Demand', 'Above Average Demand'],
            index=0,
            key='revenue_scenario_select_fin'
        )
    
    with col2:
        # Industry standard default growth rates
        if selected_revenue == 'Weak Demand':
            default_growth = 3.0
        elif selected_revenue == 'Above Average Demand':
            default_growth = 12.0
        else:
            default_growth = 7.0
            
        growth_rate = st.number_input(
            'Annual Revenue Growth Rate (%)',
            min_value=-2.0,
            max_value=20.0,
            value=default_growth,
            step=0.5,
            help="Industry standard growth rates: Weak=3%, Average=7%, Above Average=12%"
        )
    
    # Cost controls
    col3, col4 = st.columns(2)
    with col3:
        cost_scenario = st.selectbox(
            'Select Cost Scenario',
            ['Average Costs', 'Below Average Costs', 'Above Average Costs'],
            index=0,
            key='cost_scenario_select_fin'
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
            step=0.5
        )
    
    # Discount Rate
    st.header('Valuation Parameters')
    discount_rate = st.slider(
        'Discount Rate (%)',
        min_value=8.0,
        max_value=20.0,
        value=13.0,
        step=0.5,
        help="Standard range: 10-15% for small businesses"
    )
    
    # Calculate financial metrics
    base_revenue = 530899  # Base annual revenue
    base_margin = 0.2507   # Base gross margin
    years = range(1, 11)
    
    # Calculate revenues and profits
    revenues = calculate_scenario_revenues(base_revenue, selected_revenue, growth_rate, years)
    adjusted_margins = calculate_adjusted_margins(base_margin, years, cost_growth_rate)
    profits = [rev * margin for rev, margin in zip(revenues, adjusted_margins)]
    
    # Calculate NPV metrics
    cash_flows = profits
    npv, irr, payback = calculate_npv_metrics(initial_investment, cash_flows, discount_rate)
    
    # Store values in session state for the investment report
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
    
    # Display Investment Metrics
    st.header('Investment Metrics')
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Net Present Value", f"${npv:,.0f}")
    with col2:
        st.metric("Internal Rate of Return", f"{irr:.1f}%")
    with col3:
        st.metric("Payback Period", f"{payback:.1f} years")
    
    # Revenue and Profit Projections
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
    
    # Margin Analysis
    st.header('Margin Analysis')
    
    st.write("""
    The Gross Margin Projection chart shows how your profit margins may evolve over time:
    - **Blue Line**: Shows the projected gross margin after accounting for cost increases
    - **Gray Dashed Line**: Shows the baseline gross margin of 25.07% for comparison
    - The gap between the lines represents margin erosion due to rising costs
    - Steeper decline indicates more significant impact from cost growth
    - This analysis helps identify when cost management or price adjustments may be needed
    """)
    
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
    
    # Financial Summary
    st.header('Financial Summary')
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader('Revenue Metrics')
        st.write(f"Year 1 Revenue: ${revenues[0]:,.0f}")
        st.write(f"Year 10 Revenue: ${revenues[-1]:,.0f}")
        st.write(f"Average Annual Revenue: ${sum(revenues)/len(revenues):,.0f}")
        st.write(f"Total Revenue Growth: {((revenues[-1]/revenues[0] - 1) * 100):,.1f}%")
    
    with col2:
        st.subheader('Profit Metrics')
        st.write(f"Year 1 Profit: ${profits[0]:,.0f}")
        st.write(f"Year 10 Profit: ${profits[-1]:,.0f}")
        st.write(f"Average Annual Profit: ${sum(profits)/len(profits):,.0f}")
        st.write(f"Final Year Margin: {(profits[-1]/revenues[-1] * 100):,.1f}%")
    
    # Sensitivity Analysis (Tornado Plot)
    st.header('Sensitivity Analysis')
    
    # Create base parameters dictionary
    base_params = {
        'initial_investment': initial_investment,
        'base_revenue': base_revenue,
        'growth_rate': growth_rate,
        'discount_rate': discount_rate,
        'cost_growth': cost_growth_rate
    }
    
    # Create and display tornado plot
    tornado_fig = create_tornado_plot(base_params)
    st.plotly_chart(tornado_fig, use_container_width=True)
    
    st.write("""
    This tornado plot shows how changes in key input parameters affect the NPV:
    - Bars extending to the right (blue) show the impact of increasing the parameter
    - Bars extending to the left (red) show the impact of decreasing the parameter
    - Longer bars indicate higher sensitivity to that parameter
    - Parameters are sorted by their impact magnitude
    """)

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
    The business is projected to grow from ${revenues[0]:,.0f} to ${year_10_revenue:,.0f} in Year 10, 
    with an annual growth rate of {growth_rate:.1f}%. 
    
    Key revenue metrics:
    * Year 1 Revenue: ${revenues[0]:,.0f}
    * Year 10 Revenue: ${year_10_revenue:,.0f}
    * Average Annual Revenue: ${avg_revenue:,.0f}
    * Total Growth: {((year_10_revenue/revenues[0] - 1) * 100):.1f}%
    
    Profitability metrics:
    * Year 1 Profit: ${profits[0]:,.0f}
    * Year 10 Profit: ${year_10_profit:,.0f}
    * Average Annual Profit: ${avg_profit:,.0f}
    * Final Year Margin: {(final_margin * 100):.1f}%
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

class PDF(FPDF):
    def header(self):
        # Add logo or header if desired
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Franchise Investment Analysis Report', 0, 1, 'C')
        self.ln(10)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_pdf_report(report_content):
    """Convert markdown report to PDF format"""
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Format title
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Investment Analysis Report', ln=True)
    pdf.ln(10)
    
    # Format sections
    sections = report_content.split('##')
    for section in sections[1:]:  # Skip first empty section
        # Section title
        title = section.split('\n')[0].strip()
        content = '\n'.join(section.split('\n')[1:]).strip()
        
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, title, ln=True)
        pdf.ln(5)
        
        # Section content
        pdf.set_font('Arial', '', 12)
        # Handle bullet points
        for line in content.split('\n'):
            if line.strip().startswith('*'):
                pdf.cell(10)  # Indent
                pdf.multi_cell(0, 10, '• ' + line.strip('* '))
            else:
                pdf.multi_cell(0, 10, line.strip())
        pdf.ln(5)
    
    return pdf

def investment_report_tab():
    st.title('Investment Analysis Report')
    
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
        
        # Generate report
        report = generate_investment_report(
            npv, irr, payback, initial_investment, revenues, profits, 
            adjusted_margins, cost_growth_rate, growth_rate, 
            selected_revenue, cost_scenario
        )
        
        # Display report in Streamlit
        st.markdown(report)
        
        # Create PDF
        pdf = create_pdf_report(report)
        
        # Save PDF to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            pdf.output(tmp_file.name)
            
            # Add download button
            with open(tmp_file.name, 'rb') as pdf_file:
                pdf_bytes = pdf_file.read()
                st.download_button(
                    label="Download PDF Report",
                    data=pdf_bytes,
                    file_name="franchise_investment_analysis.pdf",
                    mime="application/pdf"
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
