import streamlit as st
import random
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import traceback

class SupportSection:
    def __init__(self):
        self.faqs = self.load_faqs()
        self.guides = self.load_guides()
        self.tips = self.load_tips()
        self.whatsapp_number = "+34694400373"  # Your WhatsApp number
    
    def load_faqs(self):
        """Load FAQ data - you can easily add/edit FAQs here"""
        return [
            {
                "category": "Getting Started",
                "question": "How do I create my first vignette?",
                "answer": "Click '📝 New Vignette' in the sidebar. Choose a session, add your memories, and save. Your vignettes will appear in the timeline."
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
                "answer": "All data is stored locally in your browser's session. Nothing is sent to external servers except the AI prompts you explicitly send."
            },
            {
                "category": "Privacy & Data",
                "question": "Will I lose my data if I close the browser?",
                "answer": "Yes, currently data is session-only. Use the 'Publish Your Book' feature to export your stories."
            },
            {
                "category": "Publishing",
                "question": "How do I export my stories?",
                "answer": "Go to 'Publish Your Book' and choose your format (PDF, Word, EPUB, or text). You can compile all vignettes into a book."
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
    
    def send_support_email(self, name, email, issue_type, message):
        """Send support email using the app's email config"""
        try:
            # Get email config from session state or st.secrets
            email_config = {
                "smtp_server": st.secrets.get("SMTP_SERVER", "smtp.gmail.com"),
                "smtp_port": int(st.secrets.get("SMTP_PORT", 587)),
                "sender_email": st.secrets.get("SENDER_EMAIL", ""),
                "sender_password": st.secrets.get("SENDER_PASSWORD", ""),
                "use_tls": True
            }
            
            if not email_config['sender_email'] or not email_config['sender_password']:
                st.error("Email configuration missing. Please contact support directly via WhatsApp.")
                return False
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = email_config['sender_email']
            msg['To'] = email_config['sender_email']  # Send to yourself
            msg['Subject'] = f"Tell My Story Support: {issue_type} from {name}"
            
            # Email body
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>📚 Tell My Story - Support Request</h2>
                
                <table style="border-collapse: collapse; width: 100%;">
                    <tr>
                        <td style="padding: 10px; background: #f0f0f0; font-weight: bold;">Name:</td>
                        <td style="padding: 10px;">{name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; background: #f0f0f0; font-weight: bold;">Email:</td>
                        <td style="padding: 10px;">{email}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; background: #f0f0f0; font-weight: bold;">Issue Type:</td>
                        <td style="padding: 10px;">{issue_type}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; background: #f0f0f0; font-weight: bold;">User ID:</td>
                        <td style="padding: 10px;">{st.session_state.get('user_id', 'Not logged in')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; background: #f0f0f0; font-weight: bold;">Time:</td>
                        <td style="padding: 10px;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
                    </tr>
                </table>
                
                <h3>Message:</h3>
                <div style="background: #f9f9f9; padding: 15px; border-left: 4px solid #667eea;">
                    {message.replace(chr(10), '<br>')}
                </div>
                
                <hr>
                <p style="color: #666; font-size: 12px;">Sent from Tell My Story Support</p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            with smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port']) as server:
                if email_config['use_tls']:
                    server.starttls()
                server.login(email_config['sender_email'], email_config['sender_password'])
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            print(f"Email error: {traceback.format_exc()}")
            return False
    
    def render_disclaimer(self):
        """Render the complete disclaimer section"""
        
        st.markdown("""
        <div style="
            background-color: #f8f9fa;
            border-left: 4px solid #6c757d;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
        ">
            <h3 style="color: #2c3e50; margin-top: 0;">📋 IMPORTANT DISCLAIMER</h3>
        """, unsafe_allow_html=True)
        
        # Plain text date - no HTML
        st.markdown("**Last Updated: February 21, 2026**")
        
        # Create expandable sections for each part of the disclaimer
        with st.expander("1. ACCURACY OF CONTENT", expanded=True):
            st.markdown("""
            The biographical content, stories, and personal narratives created using Tell My Story are based entirely on information, memories, and materials provided by you, the user. While we strive to assist you in creating well-written narratives, we cannot independently verify the factual accuracy of:
            
            - Personal memories, dates, and historical events
            - Family histories and genealogical information
            - Stories about other individuals
            - Photographs and their metadata
            - Documents and other uploaded materials
            
            **You are solely responsible for ensuring the accuracy of all information you input into the application.**
            """)
        
        with st.expander("2. AI-GENERATED CONTENT", expanded=True):
            st.markdown("""
            Tell My Story uses artificial intelligence (AI) tools including OpenAI's GPT models to provide:
            - Spelling and grammar correction
            - Writing assistance and rewrites
            - Beta reader feedback and analysis
            - Writing suggestions and improvements
            
            **IMPORTANT:** AI-generated suggestions are provided as assists only. You should review all AI-generated content for accuracy, appropriateness, and alignment with your voice before using it in your final work. AI may occasionally generate incorrect information or content that doesn't accurately reflect your intended meaning.
            """)
        
        with st.expander("3. PRIVACY & DATA HANDLING", expanded=True):
            st.markdown("""
            - Your stories and personal information are stored locally or on your own secure servers
            - We do not train AI models on your personal data
            - Content sent to OpenAI for AI features (spell check, rewrites, beta reading) is processed according to OpenAI's API data usage policies
            - You retain full ownership and copyright of all content you create
            - We recommend not including sensitive personal information like social security numbers, financial account details, or passwords
            """)
        
        with st.expander("4. LEGAL CONSIDERATIONS FOR BIOGRAPHIES", expanded=True):
            st.markdown("""
            When writing about real people (including family members, friends, or colleagues), you are responsible for:
            
            - **Defamation:** Ensuring your stories do not contain false statements that could harm someone's reputation
            - **Privacy Rights:** Respecting the privacy of living individuals
            - **Copyright:** Obtaining necessary permissions for quoted materials, letters, or third-party content
            - **Right of Publicity:** Understanding laws regarding using names or likenesses of living persons
            
            **We strongly recommend consulting with a legal professional if your biography includes potentially sensitive content about living individuals.**
            """)
        
        with st.expander("5. NO LEGAL OR PROFESSIONAL ADVICE", expanded=True):
            st.markdown("""
            Tell My Story is a writing tool and does not provide:
            - Legal advice regarding publishing, defamation, or privacy laws
            - Professional counseling or therapeutic services
            - Medical or mental health advice
            - Financial or investment guidance
            
            If you need professional advice in these areas, please consult qualified professionals.
            """)
        
        with st.expander("6. BETA READER FEEDBACK", expanded=True):
            st.markdown("""
            The Beta Reader feature provides AI-generated feedback on your writing. This feedback is:
            - Generated by artificial intelligence, not human readers
            - Intended for informational and improvement purposes only
            - Not a substitute for professional editing services
            - Based on patterns in your writing, not absolute literary judgment
            """)
        
        with st.expander("7. EXPORTED FILES", expanded=True):
            st.markdown("""
            When you export your book in DOCX, HTML, EPUB, or RTF formats:
            - Formatting may vary slightly depending on the software used to open the files
            - We recommend previewing exported files before final distribution
            - Embedded images may appear differently across various devices and readers
            """)
        
        with st.expander("8. THIRD-PARTY SERVICES", expanded=True):
            st.markdown("""
            Tell My Story may integrate with third-party services including:
            - OpenAI (for AI writing features)
            - Email services (for account notifications)
            
            Your use of these features is subject to the terms of service and privacy policies of these third-party providers.
            """)
        
        with st.expander("9. NO WARRANTIES", expanded=True):
            st.markdown("""
            Tell My Story is provided "as is" without any warranties, express or implied. We do not guarantee that:
            - The application will be error-free or uninterrupted
            - AI features will produce perfect results
            - Exported files will be compatible with all software versions
            - Your data will never be lost (please maintain your own backups)
            """)
        
        with st.expander("10. LIMITATION OF LIABILITY", expanded=True):
            st.markdown("""
            To the maximum extent permitted by law, Tell My Story and its creators shall not be liable for any indirect, incidental, special, consequential, or punitive damages, including without limitation, loss of profits, data, use, goodwill, or other intangible losses, resulting from:
            - Your use or inability to use the application
            - Any content created using the application
            - Unauthorized access to or alteration of your content
            - Statements or conduct of any third party
            """)
        
        with st.expander("11. YOUR ACKNOWLEDGMENT", expanded=True):
            st.markdown("""
            **BY USING TELL MY STORY, YOU ACKNOWLEDGE THAT YOU HAVE READ THIS DISCLAIMER AND AGREE TO BE BOUND BY ITS TERMS.**
            
            ---
            
            *For questions about this disclaimer, please contact support.*
            """)
        
        # Add download button for disclaimer
        disclaimer_text = """# DISCLAIMER - Tell My Story

**Last Updated: February 21, 2026**

## 1. ACCURACY OF CONTENT
The biographical content, stories, and personal narratives created using Tell My Story are based entirely on information, memories, and materials provided by you, the user. While we strive to assist you in creating well-written narratives, we cannot independently verify the factual accuracy of:

- Personal memories, dates, and historical events
- Family histories and genealogical information
- Stories about other individuals
- Photographs and their metadata
- Documents and other uploaded materials

**You are solely responsible for ensuring the accuracy of all information you input into the application.**

## 2. AI-GENERATED CONTENT
Tell My Story uses artificial intelligence (AI) tools including OpenAI's GPT models to provide:
- Spelling and grammar correction
- Writing assistance and rewrites
- Beta reader feedback and analysis
- Writing suggestions and improvements

**IMPORTANT:** AI-generated suggestions are provided as assists only. You should review all AI-generated content for accuracy, appropriateness, and alignment with your voice before using it in your final work. AI may occasionally generate incorrect information or content that doesn't accurately reflect your intended meaning.

## 3. PRIVACY & DATA HANDLING
- Your stories and personal information are stored locally or on your own secure servers
- We do not train AI models on your personal data
- Content sent to OpenAI for AI features (spell check, rewrites, beta reading) is processed according to OpenAI's API data usage policies
- You retain full ownership and copyright of all content you create
- We recommend not including sensitive personal information like social security numbers, financial account details, or passwords

## 4. LEGAL CONSIDERATIONS FOR BIOGRAPHIES
When writing about real people (including family members, friends, or colleagues), you are responsible for:

- **Defamation:** Ensuring your stories do not contain false statements that could harm someone's reputation
- **Privacy Rights:** Respecting the privacy of living individuals
- **Copyright:** Obtaining necessary permissions for quoted materials, letters, or third-party content
- **Right of Publicity:** Understanding laws regarding using names or likenesses of living persons

**We strongly recommend consulting with a legal professional if your biography includes potentially sensitive content about living individuals.**

## 5. NO LEGAL OR PROFESSIONAL ADVICE
Tell My Story is a writing tool and does not provide:
- Legal advice regarding publishing, defamation, or privacy laws
- Professional counseling or therapeutic services
- Medical or mental health advice
- Financial or investment guidance

If you need professional advice in these areas, please consult qualified professionals.

## 6. BETA READER FEEDBACK
The Beta Reader feature provides AI-generated feedback on your writing. This feedback is:
- Generated by artificial intelligence, not human readers
- Intended for informational and improvement purposes only
- Not a substitute for professional editing services
- Based on patterns in your writing, not absolute literary judgment

## 7. EXPORTED FILES
When you export your book in DOCX, HTML, EPUB, or RTF formats:
- Formatting may vary slightly depending on the software used to open the files
- We recommend previewing exported files before final distribution
- Embedded images may appear differently across various devices and readers

## 8. THIRD-PARTY SERVICES
Tell My Story may integrate with third-party services including:
- OpenAI (for AI writing features)
- Email services (for account notifications)

Your use of these features is subject to the terms of service and privacy policies of these third-party providers.

## 9. NO WARRANTIES
Tell My Story is provided "as is" without any warranties, express or implied. We do not guarantee that:
- The application will be error-free or uninterrupted
- AI features will produce perfect results
- Exported files will be compatible with all software versions
- Your data will never be lost (please maintain your own backups)

## 10. LIMITATION OF LIABILITY
To the maximum extent permitted by law, Tell My Story and its creators shall not be liable for any indirect, incidental, special, consequential, or punitive damages, including without limitation, loss of profits, data, use, goodwill, or other intangible losses, resulting from:
- Your use or inability to use the application
- Any content created using the application
- Unauthorized access to or alteration of your content
- Statements or conduct of any third party

## 11. YOUR ACKNOWLEDGMENT
**BY USING TELL MY STORY, YOU ACKNOWLEDGE THAT YOU HAVE READ THIS DISCLAIMER AND AGREE TO BE BOUND BY ITS TERMS.**

---

*For questions about this disclaimer, please contact support.*
"""
        
        st.download_button(
            label="📥 Download Disclaimer as Text File",
            data=disclaimer_text,
            file_name="Tell_My_Story_Disclaimer.txt",
            mime="text/plain",
            use_container_width=True
        )
    
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
        .privacy-card {
            background: #e8f4fd;
            padding: 1.5rem;
            border-radius: 10px;
            border-left: 4px solid #0366d6;
            margin: 1rem 0;
        }
        .ai-card {
            background: #f0e7ff;
            padding: 1.5rem;
            border-radius: 10px;
            border-left: 4px solid #764ba2;
            margin: 1rem 0;
        }
        .whatsapp-button {
            display: inline-block;
            background: #25D366;
            color: white;
            padding: 12px 24px;
            border-radius: 50px;
            text-decoration: none;
            font-weight: bold;
            margin: 10px 0;
            border: none;
            cursor: pointer;
            font-size: 18px;
        }
        .whatsapp-button:hover {
            background: #128C7E;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Header
        st.markdown("""
        <div class="support-header">
            <h1>📚 Help & Support</h1>
            <p>Find answers, guides, and information about how your stories are protected</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Create tabs for different support sections
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "🔍 Search FAQs", 
            "📖 Quick Guides", 
            "💡 Tips & Tricks",
            "⚖️ Why It's OK to Use AI to Write Your Life Story",
            "🔒 Why our AI won't steal your Story",
            "✉️ Contact Support",
            "📋 Disclaimer"
        ])
        
        with tab1:
            self.render_searchable_faqs()
        
        with tab2:
            self.render_guides()
        
        with tab3:
            self.render_tips()
        
        with tab4:
            self.render_ai_ethics()
        
        with tab5:
            self.render_privacy_api()
        
        with tab6:
            self.render_contact_support()
        
        with tab7:
            self.render_disclaimer()
    
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
    
    def render_ai_ethics(self):
        """Render AI & Copyright section with your exact title"""
        
        st.markdown("""
        <div class="ai-card">
            <h2>⚖️ Why It's OK to Use AI to Write Your Life Story</h2>
            <p><strong>The short answer:</strong> US courts have ruled that AI training is protected as "fair use" - the AI learns from published works the same way humans do, by reading widely and finding patterns, not by copying or storing anyone's content.</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### What Actually Happens
            
            - **AI reads** millions of books and articles - like a person in a library
            - **It learns patterns** - how sentences flow, how stories are structured
            - **It does NOT store** copies of the original works. The model is too small to hold millions of books
            
            ### What the Courts Said
            
            In June 2025, two federal court decisions (Bartz v. Anthropic and Kadrey v. Meta) ruled that:
            
            > *"Training AI on published works is 'spectacularly transformative' - it extracts uncopyrightable facts and patterns, not protected expression. This is fair use."*
            
            Importantly, in both cases, **plaintiffs could not show a single instance** where the AI reproduced protected content from their books. The models have filters preventing regurgitation.
            """)
        
        with col2:
            st.markdown("""
            ### The Human Analogy
            
            A chef who's eaten thousands of meals doesn't carry those meals in their pocket - they've just learned what works. AI learns the same way.
            
            ### What About Pirated Copies?
            
            The courts drew a clear line: **lawfully obtained content = fair use**. The only legal problems arise when companies download **pirated copies** from illegal torrent sites. 
            
            **You're using a licensed API** - not downloading pirated books. That's the key distinction.
            
            ### Bottom Line
            
            ✅ **Courts say AI training = transformative fair use**  
            ✅ **AI models don't store or copy your content**  
            ✅ **You're using a licensed API - not pirated materials**  
            ✅ **The AI helps you write YOUR story, in YOUR voice**
            """)
        
        st.markdown("---")
        st.markdown("📚 **Source:** Bartz v. Anthropic (N.D. Cal. June 2025); Kadrey v. Meta (N.D. Cal. June 2025)")
    
    def render_privacy_api(self):
        """Render Privacy & API section with your exact title"""
        
        st.markdown("""
        <div class="privacy-card">
            <h2>🔒 Why our AI won't steal your Story</h2>
            <p><strong>The short answer:</strong> We use the OpenAI API (not ChatGPT), which has fundamentally different privacy rules. Your data stays yours - we don't train on it, and OpenAI can't use it to improve their models.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Comparison table
        st.markdown("### The Critical Difference: API vs. Consumer Chat")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div style="background: #e8f4fd; padding: 1rem; border-radius: 10px;">
                <h4 style="color: #0366d6; text-align: center;">✅ API (What We Use)</h4>
                <ul>
                    <li>❌ <strong>NO training</strong> on your data by default</li>
                    <li>Your prompts and stories stay completely private</li>
                    <li>Governed by customer agreements, not privacy policy</li>
                    <li>Data retained 30 days for abuse monitoring, then deleted</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="background: #fee; padding: 1rem; border-radius: 10px;">
                <h4 style="color: #c00; text-align: center;">⚠️ Consumer ChatGPT</h4>
                <ul>
                    <li>✅ <strong>DOES train</strong> on your conversations by default</li>
                    <li>Your chats help improve OpenAI's models</li>
                    <li>Governed by consumer privacy policy</li>
                    <li>Conversations stored indefinitely</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### What "No Training" Actually Means
            
            When you use this app:
            
            1. **Your stories are not used to train future AI models** - OpenAI's business customers get this guarantee in their contracts 
            
            2. **OpenAI cannot see your data** - It's encrypted in transit and at rest 
            
            3. **Your prompts are ephemeral** - They're processed to generate responses, then retained for only 30 days for safety monitoring before permanent deletion 
            
            4. **You own everything** - Your inputs and the AI's outputs belong to you 
            """)
        
        with col2:
            st.markdown("""
            ### The Court Case That Proves This Matters
            
            In January 2026, a federal court ordered OpenAI to produce **20 million ChatGPT conversation logs** as evidence in a copyright lawsuit . 
            
            **Key fact:** Those were **consumer ChatGPT logs**. API customer data was never part of this order because different rules apply.
            
            ### Bottom Line
            
            ✅ **We use the API, not consumer ChatGPT** - This is the fundamental difference  
            ✅ **No training on your data** - Guaranteed in OpenAI's business terms   
            ✅ **30-day retention, then deletion** - Only for safety monitoring   
            ✅ **Encryption everywhere** - AES-256 at rest, TLS 1.2+ in transit   
            ✅ **You own your stories** - Not us, not OpenAI
            """)
    
    def render_contact_support(self):
        """Render contact/support form with WhatsApp only - sends emails to you"""
        
        st.markdown("### 📧 Get in Touch")
        
        col1, col2 = st.columns(2)
        
        with col1:
            with st.form("support_form"):
                name = st.text_input("Your Name")
                email = st.text_input("Your Email Address")
                issue_type = st.selectbox(
                    "Issue Type",
                    ["Bug Report", "Feature Request", "Question", "Other"]
                )
                message = st.text_area("Message", height=150)
                
                submitted = st.form_submit_button("📤 Send Message", use_container_width=True)
                
                if submitted:
                    if name and email and message:
                        with st.spinner("Sending message..."):
                            success = self.send_support_email(name, email, issue_type, message)
                            if success:
                                st.success("✅ Message sent! We'll respond within 24-48 hours.")
                            else:
                                st.error("Failed to send email. Please try WhatsApp instead.")
                    else:
                        st.error("Please fill in all fields")
        
        with col2:
            st.markdown("""
            ### 💬 WhatsApp Support
            
            Get quick help via WhatsApp. Response time: Usually within a few hours.
            """)
            
            # Format WhatsApp number for link
            whatsapp_link = f"https://wa.me/{self.whatsapp_number.replace('+', '').replace(' ', '').replace('(', '').replace(')', '').replace('-', '')}"
            
            # WhatsApp button
            st.markdown(f'''
            <a href="{whatsapp_link}" target="_blank">
                <button style="
                    background: #25D366;
                    color: white;
                    padding: 15px 32px;
                    text-align: center;
                    text-decoration: none;
                    display: inline-block;
                    font-size: 18px;
                    font-weight: bold;
                    margin: 4px 2px;
                    cursor: pointer;
                    border: none;
                    border-radius: 50px;
                    width: 100%;
                ">
                    💬 Chat on WhatsApp
                </button>
            </a>
            ''', unsafe_allow_html=True)
            
            st.markdown(f"**WhatsApp Number:** {self.whatsapp_number}")
            
            st.markdown("---")
            
            # Feedback buttons
            st.markdown("### Was this helpful?")
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                if st.button("👍 Yes", use_container_width=True):
                    st.toast("Thanks for your feedback!")
            with col_b:
                if st.button("👎 No", use_container_width=True):
                    st.toast("Sorry to hear that. Please contact support!")
            with col_c:
                if st.button("📋 Report Issue", use_container_width=True):
                    st.info("Please use the contact form or WhatsApp.")

# Usage example
if __name__ == "__main__":
    st.set_page_config(page_title="Support Center", page_icon="📚")
    
    # Initialize and render support section
    support = SupportSection()
    support.render()
