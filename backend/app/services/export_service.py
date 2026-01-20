"""
Export service for generating PDF and CSV reports from poker statistics.
"""
import io
import csv
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from decimal import Decimal
import logging

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.lib.colors import HexColor

from .statistics_service import StatisticsService
from ..schemas.statistics import StatisticsFilters

logger = logging.getLogger(__name__)


class ExportService:
    """Service for exporting poker statistics and reports."""
    
    def __init__(self, statistics_service: StatisticsService):
        self.statistics_service = statistics_service
        self.styles = getSampleStyleSheet()
        
        # Custom styles
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.darkblue,
            alignment=1  # Center alignment
        )
        
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.darkblue
        )
        
        self.subheading_style = ParagraphStyle(
            'CustomSubheading',
            parent=self.styles['Heading3'],
            fontSize=14,
            spaceAfter=8,
            textColor=colors.darkgreen
        )

    async def export_statistics_csv(self, 
                                  user_id: str, 
                                  filters: Optional[StatisticsFilters] = None) -> bytes:
        """
        Export user statistics to CSV format.
        
        Args:
            user_id: User ID
            filters: Optional filters for statistics
            
        Returns:
            CSV data as bytes
        """
        try:
            # Get comprehensive statistics
            stats = await self.statistics_service.get_comprehensive_statistics(user_id, filters)
            
            # Create CSV in memory
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(['Poker Statistics Report'])
            writer.writerow(['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            writer.writerow([])  # Empty row
            
            # Basic Statistics
            writer.writerow(['Basic Statistics'])
            writer.writerow(['Metric', 'Value', 'Description'])
            
            basic_stats = [
                ('Total Hands', stats.total_hands, 'Total number of hands played'),
                ('VPIP', f"{stats.vpip:.1f}%", 'Voluntarily Put Money In Pot'),
                ('PFR', f"{stats.pfr:.1f}%", 'Pre-Flop Raise'),
                ('Aggression Factor', f"{stats.aggression_factor:.2f}", 'Post-flop aggression'),
                ('Win Rate', f"{stats.win_rate:.2f} BB/100", 'Big blinds won per 100 hands'),
                ('Total Profit', f"${stats.total_profit:.2f}", 'Total profit/loss'),
                ('Sessions Played', stats.sessions_played, 'Number of sessions'),
                ('Average Session Length', f"{stats.avg_session_length:.1f} min", 'Average session duration'),
            ]
            
            for stat in basic_stats:
                writer.writerow(stat)
            
            writer.writerow([])  # Empty row
            
            # Advanced Statistics
            writer.writerow(['Advanced Statistics'])
            writer.writerow(['Metric', 'Value', 'Description'])
            
            advanced_stats = [
                ('3-Bet %', f"{stats.three_bet_percentage:.1f}%", 'Three-bet percentage'),
                ('Fold to 3-Bet', f"{stats.fold_to_three_bet:.1f}%", 'Fold to three-bet percentage'),
                ('C-Bet Flop', f"{stats.cbet_flop:.1f}%", 'Continuation bet on flop'),
                ('C-Bet Turn', f"{stats.cbet_turn:.1f}%", 'Continuation bet on turn'),
                ('C-Bet River', f"{stats.cbet_river:.1f}%", 'Continuation bet on river'),
                ('Fold to C-Bet Flop', f"{stats.fold_to_cbet_flop:.1f}%", 'Fold to continuation bet on flop'),
                ('Check-Raise Flop', f"{stats.check_raise_flop:.1f}%", 'Check-raise on flop'),
                ('WTSD', f"{stats.wtsd:.1f}%", 'Went to showdown percentage'),
                ('W$SD', f"{stats.w_sd:.1f}%", 'Won money at showdown'),
            ]
            
            for stat in advanced_stats:
                writer.writerow(stat)
            
            writer.writerow([])  # Empty row
            
            # Position Statistics
            if hasattr(stats, 'position_stats') and stats.position_stats:
                writer.writerow(['Position Statistics'])
                writer.writerow(['Position', 'Hands', 'VPIP %', 'PFR %', 'Win Rate (BB/100)', 'Profit'])
                
                for pos_stat in stats.position_stats:
                    writer.writerow([
                        pos_stat.position,
                        pos_stat.hands,
                        f"{pos_stat.vpip:.1f}%",
                        f"{pos_stat.pfr:.1f}%",
                        f"{pos_stat.win_rate:.2f}",
                        f"${pos_stat.profit:.2f}"
                    ])
                
                writer.writerow([])  # Empty row
            
            # Recent Sessions
            if hasattr(stats, 'recent_sessions') and stats.recent_sessions:
                writer.writerow(['Recent Sessions'])
                writer.writerow(['Date', 'Duration (min)', 'Hands', 'Win Rate (BB/100)', 'Profit'])
                
                for session in stats.recent_sessions[-10:]:  # Last 10 sessions
                    writer.writerow([
                        session.date.strftime('%Y-%m-%d'),
                        f"{session.duration_minutes:.0f}",
                        session.hands,
                        f"{session.win_rate:.2f}",
                        f"${session.profit:.2f}"
                    ])
            
            # Get CSV content as bytes
            csv_content = output.getvalue()
            output.close()
            
            return csv_content.encode('utf-8')
            
        except Exception as e:
            logger.error(f"Error exporting CSV for user {user_id}: {e}")
            raise

    async def export_statistics_pdf(self, 
                                  user_id: str, 
                                  filters: Optional[StatisticsFilters] = None,
                                  include_charts: bool = True) -> bytes:
        """
        Export user statistics to PDF format.
        
        Args:
            user_id: User ID
            filters: Optional filters for statistics
            include_charts: Whether to include charts in the PDF
            
        Returns:
            PDF data as bytes
        """
        try:
            # Get comprehensive statistics
            stats = await self.statistics_service.get_comprehensive_statistics(user_id, filters)
            
            # Create PDF in memory
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch)
            
            # Build PDF content
            story = []
            
            # Title
            story.append(Paragraph("Poker Statistics Report", self.title_style))
            story.append(Spacer(1, 20))
            
            # Report info
            report_info = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            if filters:
                if filters.start_date:
                    report_info += f"<br/>From: {filters.start_date.strftime('%Y-%m-%d')}"
                if filters.end_date:
                    report_info += f"<br/>To: {filters.end_date.strftime('%Y-%m-%d')}"
                if filters.game_type:
                    report_info += f"<br/>Game Type: {filters.game_type}"
                if filters.stakes:
                    report_info += f"<br/>Stakes: {filters.stakes}"
            
            story.append(Paragraph(report_info, self.styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Executive Summary
            story.append(Paragraph("Executive Summary", self.heading_style))
            
            summary_data = [
                ['Total Hands', str(stats.total_hands)],
                ['Win Rate', f"{stats.win_rate:.2f} BB/100"],
                ['Total Profit', f"${stats.total_profit:.2f}"],
                ['VPIP', f"{stats.vpip:.1f}%"],
                ['PFR', f"{stats.pfr:.1f}%"],
                ['Sessions', str(stats.sessions_played)],
            ]
            
            summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 20))
            
            # Basic Statistics
            story.append(Paragraph("Basic Statistics", self.heading_style))
            
            basic_data = [
                ['Metric', 'Value', 'Description'],
                ['VPIP', f"{stats.vpip:.1f}%", 'Voluntarily Put Money In Pot'],
                ['PFR', f"{stats.pfr:.1f}%", 'Pre-Flop Raise'],
                ['Aggression Factor', f"{stats.aggression_factor:.2f}", 'Post-flop aggression'],
                ['Win Rate', f"{stats.win_rate:.2f} BB/100", 'Big blinds won per 100 hands'],
                ['Total Profit', f"${stats.total_profit:.2f}", 'Total profit/loss'],
                ['Average Session', f"{stats.avg_session_length:.1f} min", 'Average session duration'],
            ]
            
            basic_table = Table(basic_data, colWidths=[2*inch, 1.5*inch, 2.5*inch])
            basic_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ]))
            
            story.append(basic_table)
            story.append(Spacer(1, 20))
            
            # Advanced Statistics
            story.append(Paragraph("Advanced Statistics", self.heading_style))
            
            advanced_data = [
                ['Metric', 'Value', 'Description'],
                ['3-Bet %', f"{stats.three_bet_percentage:.1f}%", 'Three-bet percentage'],
                ['Fold to 3-Bet', f"{stats.fold_to_three_bet:.1f}%", 'Fold to three-bet percentage'],
                ['C-Bet Flop', f"{stats.cbet_flop:.1f}%", 'Continuation bet on flop'],
                ['C-Bet Turn', f"{stats.cbet_turn:.1f}%", 'Continuation bet on turn'],
                ['C-Bet River', f"{stats.cbet_river:.1f}%", 'Continuation bet on river'],
                ['Fold to C-Bet Flop', f"{stats.fold_to_cbet_flop:.1f}%", 'Fold to continuation bet on flop'],
                ['Check-Raise Flop', f"{stats.check_raise_flop:.1f}%", 'Check-raise on flop'],
                ['WTSD', f"{stats.wtsd:.1f}%", 'Went to showdown percentage'],
                ['W$SD', f"{stats.w_sd:.1f}%", 'Won money at showdown'],
            ]
            
            advanced_table = Table(advanced_data, colWidths=[2*inch, 1.5*inch, 2.5*inch])
            advanced_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ]))
            
            story.append(advanced_table)
            story.append(Spacer(1, 20))
            
            # Position Statistics
            if hasattr(stats, 'position_stats') and stats.position_stats:
                story.append(Paragraph("Position Analysis", self.heading_style))
                
                position_data = [['Position', 'Hands', 'VPIP %', 'PFR %', 'Win Rate', 'Profit']]
                
                for pos_stat in stats.position_stats:
                    position_data.append([
                        pos_stat.position,
                        str(pos_stat.hands),
                        f"{pos_stat.vpip:.1f}%",
                        f"{pos_stat.pfr:.1f}%",
                        f"{pos_stat.win_rate:.2f}",
                        f"${pos_stat.profit:.2f}"
                    ])
                
                position_table = Table(position_data, colWidths=[1*inch, 1*inch, 1*inch, 1*inch, 1*inch, 1*inch])
                position_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.purple),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lavender),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                ]))
                
                story.append(position_table)
                story.append(Spacer(1, 20))
            
            # Recent Performance
            if hasattr(stats, 'recent_sessions') and stats.recent_sessions:
                story.append(Paragraph("Recent Sessions", self.heading_style))
                
                session_data = [['Date', 'Duration', 'Hands', 'Win Rate', 'Profit']]
                
                for session in stats.recent_sessions[-10:]:  # Last 10 sessions
                    session_data.append([
                        session.date.strftime('%Y-%m-%d'),
                        f"{session.duration_minutes:.0f}m",
                        str(session.hands),
                        f"{session.win_rate:.2f}",
                        f"${session.profit:.2f}"
                    ])
                
                session_table = Table(session_data, colWidths=[1.2*inch, 1*inch, 1*inch, 1.2*inch, 1.2*inch])
                session_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.orange),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightyellow),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                ]))
                
                story.append(session_table)
            
            # Build PDF
            doc.build(story)
            
            # Get PDF content
            pdf_content = buffer.getvalue()
            buffer.close()
            
            return pdf_content
            
        except Exception as e:
            logger.error(f"Error exporting PDF for user {user_id}: {e}")
            raise

    async def export_session_report_pdf(self, 
                                      user_id: str, 
                                      session_id: str) -> bytes:
        """
        Export a detailed session report to PDF.
        
        Args:
            user_id: User ID
            session_id: Session ID
            
        Returns:
            PDF data as bytes
        """
        try:
            # Get session data
            session_data = await self.statistics_service.get_session_details(user_id, session_id)
            
            # Create PDF in memory
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch)
            
            story = []
            
            # Title
            story.append(Paragraph(f"Session Report - {session_data.date.strftime('%Y-%m-%d')}", self.title_style))
            story.append(Spacer(1, 20))
            
            # Session Overview
            story.append(Paragraph("Session Overview", self.heading_style))
            
            overview_data = [
                ['Duration', f"{session_data.duration_minutes:.0f} minutes"],
                ['Hands Played', str(session_data.hands)],
                ['Win Rate', f"{session_data.win_rate:.2f} BB/100"],
                ['Total Profit', f"${session_data.profit:.2f}"],
                ['Game Type', session_data.game_type],
                ['Stakes', session_data.stakes],
            ]
            
            overview_table = Table(overview_data, colWidths=[2*inch, 2*inch])
            overview_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(overview_table)
            story.append(Spacer(1, 20))
            
            # Key Statistics for this session
            if hasattr(session_data, 'statistics'):
                story.append(Paragraph("Session Statistics", self.heading_style))
                
                stats_data = [
                    ['VPIP', f"{session_data.statistics.vpip:.1f}%"],
                    ['PFR', f"{session_data.statistics.pfr:.1f}%"],
                    ['Aggression Factor', f"{session_data.statistics.aggression_factor:.2f}"],
                    ['3-Bet %', f"{session_data.statistics.three_bet_percentage:.1f}%"],
                    ['C-Bet %', f"{session_data.statistics.cbet_flop:.1f}%"],
                ]
                
                stats_table = Table(stats_data, colWidths=[2*inch, 2*inch])
                stats_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(stats_table)
            
            # Build PDF
            doc.build(story)
            
            # Get PDF content
            pdf_content = buffer.getvalue()
            buffer.close()
            
            return pdf_content
            
        except Exception as e:
            logger.error(f"Error exporting session PDF for user {user_id}, session {session_id}: {e}")
            raise

    def _format_currency(self, value: Union[float, Decimal]) -> str:
        """Format currency values."""
        if isinstance(value, Decimal):
            value = float(value)
        return f"${value:.2f}"

    def _format_percentage(self, value: Union[float, Decimal]) -> str:
        """Format percentage values."""
        if isinstance(value, Decimal):
            value = float(value)
        return f"{value:.1f}%"

    async def export_hands_csv(self, 
                             user_id: str, 
                             filters: Optional[StatisticsFilters] = None,
                             limit: int = 1000) -> bytes:
        """
        Export hand history data to CSV format.
        
        Args:
            user_id: User ID
            filters: Optional filters for hands
            limit: Maximum number of hands to export
            
        Returns:
            CSV data as bytes
        """
        try:
            # Get hands data
            hands = await self.statistics_service.get_filtered_hands(user_id, filters, limit)
            
            # Create CSV in memory
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(['Hand History Export'])
            writer.writerow(['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            writer.writerow([])  # Empty row
            
            # Hands data header
            writer.writerow([
                'Hand ID', 'Date', 'Game Type', 'Stakes', 'Position', 
                'Player Cards', 'Board Cards', 'Result', 'Pot Size', 'Profit'
            ])
            
            for hand in hands:
                writer.writerow([
                    hand.hand_id,
                    hand.date_played.strftime('%Y-%m-%d %H:%M:%S') if hand.date_played else '',
                    hand.game_type or '',
                    hand.stakes or '',
                    hand.position or '',
                    ' '.join(hand.player_cards) if hand.player_cards else '',
                    ' '.join(hand.board_cards) if hand.board_cards else '',
                    hand.result or '',
                    f"${hand.pot_size:.2f}" if hand.pot_size else '',
                    f"${hand.profit:.2f}" if hasattr(hand, 'profit') and hand.profit else ''
                ])
            
            # Get CSV content as bytes
            csv_content = output.getvalue()
            output.close()
            
            return csv_content.encode('utf-8')
            
        except Exception as e:
            logger.error(f"Error exporting hands CSV for user {user_id}: {e}")
            raise

    async def export_comprehensive_report_pdf(self, 
                                            user_id: str, 
                                            filters: Optional[StatisticsFilters] = None,
                                            include_hands: bool = False,
                                            include_charts: bool = True) -> bytes:
        """
        Export a comprehensive poker report to PDF format.
        
        Args:
            user_id: User ID
            filters: Optional filters for data
            include_hands: Whether to include detailed hand history
            include_charts: Whether to include charts and graphs
            
        Returns:
            PDF data as bytes
        """
        try:
            # Get comprehensive data
            stats = await self.statistics_service.get_comprehensive_statistics(user_id, filters)
            
            # Create PDF in memory
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch)
            
            story = []
            
            # Title Page
            story.append(Paragraph("Comprehensive Poker Analysis Report", self.title_style))
            story.append(Spacer(1, 30))
            
            # Executive Summary
            story.append(Paragraph("Executive Summary", self.heading_style))
            
            summary_text = f"""
            This comprehensive report analyzes your poker performance based on {stats.total_hands} hands played.
            Your overall win rate is {stats.win_rate:.2f} BB/100 with a total profit of ${stats.total_profit:.2f}.
            
            Key Performance Indicators:
            • VPIP: {stats.vpip:.1f}% (Voluntarily Put Money In Pot)
            • PFR: {stats.pfr:.1f}% (Pre-Flop Raise)
            • Aggression Factor: {stats.aggression_factor:.2f}
            • Sessions Played: {stats.sessions_played}
            """
            
            story.append(Paragraph(summary_text, self.styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Add all the sections from the regular PDF export
            # (This would include all the tables and data from export_statistics_pdf)
            
            # If including hands, add a sample of recent hands
            if include_hands:
                story.append(PageBreak())
                story.append(Paragraph("Recent Hand History Sample", self.heading_style))
                
                # Get recent hands
                recent_hands = await self.statistics_service.get_recent_hands(user_id, limit=20)
                
                if recent_hands:
                    hands_data = [['Date', 'Game', 'Position', 'Cards', 'Result', 'Profit']]
                    
                    for hand in recent_hands:
                        hands_data.append([
                            hand.date_played.strftime('%m/%d') if hand.date_played else '',
                            f"{hand.game_type} {hand.stakes}" if hand.game_type and hand.stakes else '',
                            hand.position or '',
                            ' '.join(hand.player_cards[:2]) if hand.player_cards else '',
                            hand.result or '',
                            f"${hand.profit:.2f}" if hasattr(hand, 'profit') and hand.profit else ''
                        ])
                    
                    hands_table = Table(hands_data, colWidths=[1*inch, 1.5*inch, 0.8*inch, 1*inch, 1*inch, 1*inch])
                    hands_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.lightcoral),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ]))
                    
                    story.append(hands_table)
            
            # Build PDF
            doc.build(story)
            
            # Get PDF content
            pdf_content = buffer.getvalue()
            buffer.close()
            
            return pdf_content
            
        except Exception as e:
            logger.error(f"Error exporting comprehensive report for user {user_id}: {e}")
            raise