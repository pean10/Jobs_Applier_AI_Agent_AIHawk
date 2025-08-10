"""
M&A Job Application Dashboard
Streamlit-based monitoring and analytics dashboard
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
import json
from pathlib import Path

from src.ma_application_manager import MAApplicationManager
from src.logging import logger

class MADashboard:
    """Interactive dashboard for M&A job application monitoring"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.db_path = Path("data_folder/output/ma_applications.db")
        
    def run_dashboard(self):
        """Run the Streamlit dashboard"""
        st.set_page_config(
            page_title="M&A Job Application Dashboard",
            page_icon="💼",
            layout="wide"
        )
        
        st.title("🎯 M&A Job Application Dashboard")
        st.markdown("**Rockville Centre & NYC M&A Opportunities**")
        
        # Sidebar
        st.sidebar.title("Navigation")
        page = st.sidebar.selectbox(
            "Choose a page",
            ["Overview", "Applications", "Job Market", "Performance", "Settings"]
        )
        
        if page == "Overview":
            self.show_overview()
        elif page == "Applications":
            self.show_applications()
        elif page == "Job Market":
            self.show_job_market()
        elif page == "Performance":
            self.show_performance()
        elif page == "Settings":
            self.show_settings()

    def show_overview(self):
        """Show overview dashboard"""
        st.header("📊 Application Overview")
        
        # Get data
        stats = self.get_application_stats()
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Applications",
                stats.get('total_applications', 0),
                delta=stats.get('recent_applications', 0)
            )
        
        with col2:
            st.metric(
                "Response Rate",
                f"{stats.get('response_rate', 0)}%",
                delta=f"{stats.get('response_rate_change', 0)}%"
            )
        
        with col3:
            st.metric(
                "Active Opportunities",
                stats.get('active_opportunities', 0)
            )
        
        with col4:
            st.metric(
                "Avg M&A Score",
                f"{stats.get('avg_ma_score', 0):.1f}",
                delta=f"{stats.get('ma_score_trend', 0):.1f}"
            )
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Application status pie chart
            if stats.get('status_breakdown'):
                fig = px.pie(
                    values=list(stats['status_breakdown'].values()),
                    names=list(stats['status_breakdown'].keys()),
                    title="Application Status Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Applications over time
            timeline_data = self.get_application_timeline()
            if not timeline_data.empty:
                fig = px.line(
                    timeline_data,
                    x='date',
                    y='applications',
                    title="Applications Over Time"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Recent activity
        st.subheader("🕒 Recent Activity")
        recent_apps = self.get_recent_applications()
        if not recent_apps.empty:
            st.dataframe(recent_apps, use_container_width=True)
        else:
            st.info("No recent applications found.")

    def show_applications(self):
        """Show detailed applications view"""
        st.header("📋 Application Details")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_filter = st.selectbox(
                "Filter by Status",
                ["All", "submitted", "responded", "rejected", "interview"]
            )
        
        with col2:
            company_filter = st.selectbox(
                "Filter by Company",
                ["All"] + self.get_companies()
            )
        
        with col3:
            date_range = st.date_input(
                "Date Range",
                value=(datetime.now() - timedelta(days=30), datetime.now()),
                max_value=datetime.now()
            )
        
        # Get filtered applications
        applications = self.get_applications(status_filter, company_filter, date_range)
        
        if not applications.empty:
            # Add action buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📧 Send Follow-ups"):
                    st.success("Follow-up emails queued!")
            
            with col2:
                if st.button("📊 Export Data"):
                    csv = applications.to_csv(index=False)
                    st.download_button(
                        "Download CSV",
                        csv,
                        "ma_applications.csv",
                        "text/csv"
                    )
            
            with col3:
                if st.button("🔄 Refresh Data"):
                    st.experimental_rerun()
            
            # Applications table
            st.dataframe(
                applications,
                use_container_width=True,
                column_config={
                    "ma_relevance_score": st.column_config.ProgressColumn(
                        "M&A Score",
                        help="M&A relevance score (0-100)",
                        min_value=0,
                        max_value=100,
                    ),
                    "job_url": st.column_config.LinkColumn("Job URL"),
                }
            )
        else:
            st.info("No applications found matching the selected criteria.")

    def show_job_market(self):
        """Show job market analysis"""
        st.header("🏢 M&A Job Market Analysis")
        
        # Market overview
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Top M&A Employers")
            top_companies = self.get_top_companies()
            if not top_companies.empty:
                fig = px.bar(
                    top_companies,
                    x='applications',
                    y='company',
                    orientation='h',
                    title="Applications by Company"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("M&A Role Distribution")
            role_dist = self.get_role_distribution()
            if not role_dist.empty:
                fig = px.pie(
                    role_dist,
                    values='count',
                    names='role_type',
                    title="M&A Roles Applied To"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Geographic analysis
        st.subheader("🗺️ Geographic Distribution")
        location_data = self.get_location_analysis()
        if not location_data.empty:
            fig = px.scatter_mapbox(
                location_data,
                lat="lat",
                lon="lon",
                size="applications",
                hover_name="location",
                hover_data=["applications"],
                mapbox_style="open-street-map",
                title="M&A Job Applications by Location",
                zoom=9,
                center={"lat": 40.7128, "lon": -74.0060}  # NYC center
            )
            st.plotly_chart(fig, use_container_width=True)

    def show_performance(self):
        """Show performance analytics"""
        st.header("📈 Performance Analytics")
        
        # Response rate analysis
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Response Rate Trends")
            response_trends = self.get_response_trends()
            if not response_trends.empty:
                fig = px.line(
                    response_trends,
                    x='week',
                    y='response_rate',
                    title="Weekly Response Rate"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("M&A Score vs Response Rate")
            score_response = self.get_score_response_correlation()
            if not score_response.empty:
                fig = px.scatter(
                    score_response,
                    x='ma_relevance_score',
                    y='got_response',
                    title="M&A Score vs Response Correlation",
                    trendline="ols"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Performance insights
        st.subheader("🎯 Performance Insights")
        insights = self.generate_insights()
        for insight in insights:
            st.info(insight)

    def show_settings(self):
        """Show settings and configuration"""
        st.header("⚙️ Settings & Configuration")
        
        # Application limits
        st.subheader("Application Limits")
        col1, col2 = st.columns(2)
        
        with col1:
            daily_limit = st.number_input(
                "Daily Application Limit",
                min_value=1,
                max_value=50,
                value=15
            )
        
        with col2:
            weekly_limit = st.number_input(
                "Weekly Application Limit",
                min_value=1,
                max_value=200,
                value=75
            )
        
        # Search parameters
        st.subheader("Search Parameters")
        
        search_radius = st.slider(
            "Search Radius (miles)",
            min_value=5,
            max_value=50,
            value=25
        )
        
        min_ma_score = st.slider(
            "Minimum M&A Relevance Score",
            min_value=0,
            max_value=100,
            value=70
        )
        
        # Email settings
        st.subheader("Email Configuration")
        email_enabled = st.checkbox("Enable Follow-up Emails")
        
        if email_enabled:
            email_address = st.text_input("Email Address")
            smtp_server = st.text_input("SMTP Server", value="smtp.gmail.com")
            smtp_port = st.number_input("SMTP Port", value=587)
        
        # Save settings
        if st.button("💾 Save Settings"):
            settings = {
                'daily_limit': daily_limit,
                'weekly_limit': weekly_limit,
                'search_radius': search_radius,
                'min_ma_score': min_ma_score,
                'email_enabled': email_enabled
            }
            
            if email_enabled:
                settings.update({
                    'email_address': email_address,
                    'smtp_server': smtp_server,
                    'smtp_port': smtp_port
                })
            
            # Save to config file
            with open("data_folder/ma_config.json", "w") as f:
                json.dump(settings, f, indent=2)
            
            st.success("Settings saved successfully!")

    def get_application_stats(self) -> Dict:
        """Get application statistics from database"""
        if not self.db_path.exists():
            return {}
        
        conn = sqlite3.connect(self.db_path)
        
        try:
            # Total applications
            total_apps = pd.read_sql_query(
                "SELECT COUNT(*) as count FROM applications", conn
            ).iloc[0]['count']
            
            # Status breakdown
            status_df = pd.read_sql_query(
                "SELECT status, COUNT(*) as count FROM applications GROUP BY status", conn
            )
            status_breakdown = dict(zip(status_df['status'], status_df['count']))
            
            # Response rate
            responded = status_breakdown.get('responded', 0) + status_breakdown.get('interview', 0)
            response_rate = (responded / total_apps * 100) if total_apps > 0 else 0
            
            # Recent applications (last 7 days)
            recent_df = pd.read_sql_query(
                "SELECT COUNT(*) as count FROM applications WHERE application_date > datetime('now', '-7 days')", conn
            )
            recent_apps = recent_df.iloc[0]['count']
            
            # Average M&A score
            avg_score_df = pd.read_sql_query(
                "SELECT AVG(ma_relevance_score) as avg_score FROM applications", conn
            )
            avg_ma_score = avg_score_df.iloc[0]['avg_score'] or 0
            
            return {
                'total_applications': total_apps,
                'status_breakdown': status_breakdown,
                'response_rate': round(response_rate, 2),
                'recent_applications': recent_apps,
                'avg_ma_score': avg_ma_score,
                'active_opportunities': status_breakdown.get('submitted', 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting application stats: {e}")
            return {}
        finally:
            conn.close()

    def get_application_timeline(self) -> pd.DataFrame:
        """Get application timeline data"""
        if not self.db_path.exists():
            return pd.DataFrame()
        
        conn = sqlite3.connect(self.db_path)
        
        try:
            df = pd.read_sql_query("""
                SELECT DATE(application_date) as date, COUNT(*) as applications
                FROM applications
                GROUP BY DATE(application_date)
                ORDER BY date
            """, conn)
            
            df['date'] = pd.to_datetime(df['date'])
            return df
            
        except Exception as e:
            logger.error(f"Error getting timeline data: {e}")
            return pd.DataFrame()
        finally:
            conn.close()

    def get_recent_applications(self) -> pd.DataFrame:
        """Get recent applications"""
        if not self.db_path.exists():
            return pd.DataFrame()
        
        conn = sqlite3.connect(self.db_path)
        
        try:
            df = pd.read_sql_query("""
                SELECT job_title, company, status, application_date, ma_relevance_score
                FROM applications
                ORDER BY application_date DESC
                LIMIT 10
            """, conn)
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting recent applications: {e}")
            return pd.DataFrame()
        finally:
            conn.close()

    def get_companies(self) -> List[str]:
        """Get list of companies applied to"""
        if not self.db_path.exists():
            return []
        
        conn = sqlite3.connect(self.db_path)
        
        try:
            df = pd.read_sql_query(
                "SELECT DISTINCT company FROM applications ORDER BY company", conn
            )
            return df['company'].tolist()
            
        except Exception as e:
            logger.error(f"Error getting companies: {e}")
            return []
        finally:
            conn.close()

    def get_applications(self, status_filter: str, company_filter: str, date_range) -> pd.DataFrame:
        """Get filtered applications"""
        if not self.db_path.exists():
            return pd.DataFrame()
        
        conn = sqlite3.connect(self.db_path)
        
        try:
            query = "SELECT * FROM applications WHERE 1=1"
            params = []
            
            if status_filter != "All":
                query += " AND status = ?"
                params.append(status_filter)
            
            if company_filter != "All":
                query += " AND company = ?"
                params.append(company_filter)
            
            if len(date_range) == 2:
                query += " AND DATE(application_date) BETWEEN ? AND ?"
                params.extend([date_range[0].strftime('%Y-%m-%d'), date_range[1].strftime('%Y-%m-%d')])
            
            query += " ORDER BY application_date DESC"
            
            df = pd.read_sql_query(query, conn, params=params)
            return df
            
        except Exception as e:
            logger.error(f"Error getting applications: {e}")
            return pd.DataFrame()
        finally:
            conn.close()

    def generate_insights(self) -> List[str]:
        """Generate performance insights"""
        insights = []
        stats = self.get_application_stats()
        
        if stats.get('response_rate', 0) > 15:
            insights.append("🎉 Excellent response rate! Your applications are well-targeted.")
        elif stats.get('response_rate', 0) > 10:
            insights.append("👍 Good response rate. Consider refining your targeting.")
        else:
            insights.append("💡 Consider improving application quality or targeting more relevant roles.")
        
        if stats.get('avg_ma_score', 0) > 80:
            insights.append("🎯 High M&A relevance scores indicate excellent job targeting.")
        elif stats.get('avg_ma_score', 0) > 60:
            insights.append("📊 Moderate M&A relevance. Consider focusing on more specialized roles.")
        else:
            insights.append("🔍 Low M&A relevance scores. Review search criteria and keywords.")
        
        return insights

# Streamlit app entry point
def main():
    config = {
        'daily_application_limit': 15,
        'weekly_application_limit': 75
    }
    
    dashboard = MADashboard(config)
    dashboard.run_dashboard()

if __name__ == "__main__":
    main()