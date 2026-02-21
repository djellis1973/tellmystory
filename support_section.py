import streamlit as st
import pandas as pd
from datetime import datetime
import json

class SupportSection:
    def __init__(self):
        self.faqs = self.load_faqs()
        self.guides = self.load_guides()
        self.tips = self.load_tips()
    
    def load_faqs(self):
        """Load FAQ data - you can easily add/edit FAQs here"""
        return [
            {
                "category": "Getting Started",
                "question": "How do I create my first vignette?",
                "answer": "Click on '📝 New Vignette' in the sidebar. Choose a session, add your memories, and save. Your vignettes will appear in the timeline."
            },
            {
                "category": "Getting Started",
                "question": "What is a vignette?",
                "answer": "A vignette is a short, descriptive memory or story from your life. It can include text, photos, and emotional context."
            },
            {
                "category": "Sessions",
                "question": "How many sessions can I create?",
                "answer": "You can create unlimited sessions! Start with the 13 pre-defined life stages or create custom sessions."
            },
            {
                "category": "Sessions",
                "question": "Can I rename sessions?",
                "answer": "Yes! Go to 'Session Management' and click on 'Custom Session' to create or rename sessions."
            },
            {
                "category": "Question Banks",
                "question": "How do I switch question banks?",
                "answer": "Use the 'Bank Manager' under Tools. You can select from Life Story - Comprehensive, Quick Memories, or Legacy Focus."
            },
            {
                "category": "Question Banks",
                "question": "Can I create custom questions?",
                "answer": "Currently, you can select from pre-defined banks. Custom questions coming in a future update!"
            },
            {
                "category": "Privacy & Data",
                "question": "Where is my data stored?",
                "answer": "All data is stored locally in your browser's session. Nothing is sent to external servers."
            },
            {
                "category": "Privacy & Data",
                "question": "Will I lose my data if I close the browser?",
                "answer": "Yes, currently data is session-only. Use the 'Publish Your Book' feature to export your stories."
            },
            {
                "category": "Publishing",
                "question": "How do I export my stories?",
                "answer": "Go to 'Publish Your Book' and choose your format (PDF, Word, or text). You can compile all vignettes into a book."
            },
            {
                "category": "Publishing",
                "question": "Can I add photos to my book?",
                "answer": "Yes! Photos included in your vignettes will be exported with your book."
            },
            {
                "category": "Troubleshooting",
                "question": "The app is running slowly",
                "answer": "Try clearing your session data with 'Clear Session' or 'Clear All' buttons at the bottom of the sidebar."
            },
            {
                "category": "Troubleshooting",
                "question": "My vignettes disappeared",
                "answer": "Check if you accidentally clicked 'Clear All'. Unfortunately, this action cannot be undone."
            },
            {
                "category": "Features",
                "question": "Can I search my stories?",
                "answer": "Yes! Use the search bar at the bottom of the sidebar to search through all your answers and captions."
            },
            {
                "category": "Features",
                "question": "How do I track my writing progress?",
                "answer": "The main dashboard shows your progress, including vignette count, word count, and photos added."
            }
        ]
    
    def load_guides(self):
        """Load quick start guides and tutorials"""
        return [
            {
                "title": "Quick Start Guide",
                "content": """
                1. **Complete Your Profile** - Click 'Complete Profile' to add your basic info
                2. **Choose a Session** - Start with Session 1: Childhood
                3. **Answer Questions** - Use the question bank to guide your writing
                4. **Add Photos** - Enhance your vignettes with images
                5. **Review & Publish** - Export your stories when ready
                """,
                "icon": "🚀"
            },
            {
                "title": "Writing Tips",
                "content": """
                - **Be specific**: Include sensory details (sights, sounds, smells)
                - **Don't rush**: Take time with each memory
                - **Add context**: Explain why moments were significant
                - **Use photos**: They trigger more memories
                - **Write regularly**: Even 5 minutes daily adds up
                """,
                "icon": "✍️"
            },
            {
                "title": "Keyboard Shortcuts",
                "content": """
                - **Ctrl/Cmd + Enter**: Submit answer
                - **Ctrl/Cmd + S**: Save current vignette
                - **Ctrl/Cmd + F**: Focus search bar
                - **Esc**: Clear search or close dialogs
                """,
                "icon": "⌨️"
            }
        ]
    
    def load_tips(self):
        """Load daily tips and best practices"""
        return [
            "💡 **Tip**: Use the search bar to find specific memories across all your vignettes",
            "💡 **Tip**: Add photos to trigger more detailed memories",
            "💡 **Tip**: You can switch question banks mid-session for different perspectives",
            "💡 **Tip**: Export your stories regularly to keep backups",
            "💡 **Tip**: Use the emotion tags to track the feeling-tone of your memories"
        ]
    
    def search_faqs(self, search_term):
        """Search FAQs based on user input"""
        if not search_term:
            return self.faqs
        
        search_term = search_term.lower()
        results = []
        
        for faq in self.faqs:
            if (search_term in faq["question"].lower() or 
                search_term in faq["answer"].lower() or 
                search_term in faq["category"].lower()):
                results.append(faq)
        
        return results
    
    def render(self):
        """Render the complete support section"""
        
        # Custom CSS for better styling
        st.markdown("""
        <style>
        .support-header {
            text-align: center;
            padding: 1rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            margin-bottom: 2rem;
        }
        .faq-item {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
            margin: 0.5rem 0;
            border-left: 4px solid #667eea;
        }
        .guide-card {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin: 1rem 0;
            border: 1px solid #e0e0e0;
        }
        .tip-box {
            background: #fff3cd;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #ffc107;
            margin: 0.5rem 0;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Header
        st.markdown("""
        <div class="support-header">
            <h1>📚 Help & Support</h1>
            <p>Find answers, guides, and tips for your storytelling journey</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Create tabs for different support sections
        tab1, tab2, tab3, tab4 = st.tabs([
            "🔍 Search FAQs", 
            "📖 Quick Guides", 
            "💡 Tips & Tricks",
            "📞 Contact Support"
        ])
        
        with tab1:
            self.render_searchable_faqs()
        
        with tab2:
            self.render_guides()
        
        with tab3:
            self.render_tips()
        
        with tab4:
            self.render_contact_support()
    
    def render_searchable_faqs(self):
        """Render searchable FAQ section"""
        
        # Search box
        col1, col2 = st.columns([3, 1])
        with col1:
            search_query = st.text_input(
                "🔎 Search FAQs",
                placeholder="e.g., data, export, session, photos...",
                key="faq_search"
            )
        
        with col2:
            categories = ["All"] + sorted(list(set(faq["category"] for faq in self.faqs)))
            category_filter = st.selectbox("Filter by category", categories)
        
        # Get search results
        results = self.search_faqs(search_query)
        
        # Apply category filter
        if category_filter != "All":
            results = [faq for faq in results if faq["category"] == category_filter]
        
        # Display results
        st.markdown(f"**Found {len(results)} answers**")
        
        if results:
            # Group by category for better organization
            results_by_category = {}
            for faq in results:
                if faq["category"] not in results_by_category:
                    results_by_category[faq["category"]] = []
                results_by_category[faq["category"]].append(faq)
            
            # Display FAQs by category
            for category, faqs in results_by_category.items():
                with st.expander(f"📁 {category} ({len(faqs)})", expanded=True):
                    for faq in faqs:
                        st.markdown(f"""
                        <div class="faq-item">
                            <strong>❓ {faq['question']}</strong><br>
                            {faq['answer']}
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.info("No FAQs found matching your search. Try different keywords or contact support.")
            
            # Suggest popular topics
            st.markdown("**Popular topics:**")
            popular_topics = ["vignette", "data", "export", "session", "photos"]
            cols = st.columns(len(popular_topics))
            for i, topic in enumerate(popular_topics):
                with cols[i]:
                    if st.button(f"🔍 {topic}", key=f"topic_{topic}"):
                        # This would trigger a new search (requires session state management)
                        pass
    
    def render_guides(self):
        """Render quick guides section"""
        
        for guide in self.guides:
            with st.container():
                st.markdown(f"""
                <div class="guide-card">
                    <h3>{guide['icon']} {guide['title']}</h3>
                    {guide['content']}
                </div>
                """, unsafe_allow_html=True)
    
    def render_tips(self):
        """Render tips and tricks section"""
        
        # Random tip of the day
        import random
        tip_of_day = random.choice(self.tips)
        
        st.markdown("### 🌟 Tip of the Day")
        st.markdown(f"""
        <div class="tip-box">
            {tip_of_day}
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 📋 All Tips")
        
        # Display all tips in columns
        cols = st.columns(2)
        for i, tip in enumerate(self.tips):
            with cols[i % 2]:
                st.markdown(f"""
                <div style="background: #f8f9fa; padding: 0.8rem; border-radius: 5px; margin: 0.3rem 0;">
                    {tip}
                </div>
                """, unsafe_allow_html=True)
        
        # Add a tip submission form
        with st.expander("💭 Share a Tip"):
            with st.form("tip_form"):
                user_tip = st.text_area("Your tip:", placeholder="Share your tip for other users...")
                if st.form_submit_button("Submit Tip"):
                    st.success("Thanks for sharing! We'll review your tip.")
    
    def render_contact_support(self):
        """Render contact/support form"""
        
        st.markdown("### 📧 Get in Touch")
        
        col1, col2 = st.columns(2)
        
        with col1:
            with st.form("support_form"):
                name = st.text_input("Your Name")
                email = st.text_input("Email Address")
                issue_type = st.selectbox(
                    "Issue Type",
                    ["Bug Report", "Feature Request", "Question", "Other"]
                )
                message = st.text_area("Message", height=150)
                
                if st.form_submit_button("Send Message"):
                    if name and email and message:
                        st.success("✅ Message sent! We'll respond within 24-48 hours.")
                        # Here you would typically send an email or log to database
                    else:
                        st.error("Please fill in all fields")
        
        with col2:
            st.markdown("""
            ### 📞 Other Ways to Reach Us
            
            **Response Time:** Within 24-48 hours
            
            **Common Issues:**
            - ⚡ Bug reports: Usually fixed within 1-2 days
            - 💡 Feature requests: Reviewed monthly
            - ❓ Questions: Answered within 24 hours
            
            **Before Contacting:**
            1. Check the FAQ section
            2. Try clearing your session
            3. Refresh the page
            """)
            
            # Feedback buttons
            st.markdown("### Was this helpful?")
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                if st.button("👍 Yes"):
                    st.toast("Thanks for your feedback!")
            with col_b:
                if st.button("👎 No"):
                    st.toast("Sorry to hear that. Please contact support!")
            with col_c:
                if st.button("📋 Report Issue"):
                    st.info("Please use the contact form.")

# Usage example
if __name__ == "__main__":
    st.set_page_config(page_title="Support Center", page_icon="📚")
    
    # Initialize and render support section
    support = SupportSection()
    support.render()
