# ⚽ Mia Training Tracker - Web App

A comprehensive soccer training analytics platform with automatic Google Sheets sync, built with Streamlit.  The data structure is based on data collected by CityPlay soccer boot sensors.

## 🌟 Features

### **Data Management**
- ☁️ **Google Sheets Integration** - Automatic cloud sync and backup
- 📸 **Image Upload & OCR** - Extract data from training screenshots
- ✏️ **Smart Data Entry** - Dynamic forms with calculated fields
- 🔄 **Auto-Save** - Changes sync automatically to Google Sheets
- 🔄 **Refresh Data** - One-click data refresh from cloud

### **Analytics & Insights**
- 📊 **Dashboard** - Key performance indicators with averages and bests
- 📈 **Analytics Charts** - Detailed performance trends over time
- ⚡ **Speed Analysis** - Track explosive power and velocity
- 🔄 **Agility Metrics** - Monitor turning ability and quickness
- ⚽ **Ball Work Tracking** - Technical skill development metrics
- ⚽ **Match Play Analysis** - Game-specific performance tracking
- 🏆 **Personal Records** - All-time best performances
- 🤖 **AI Insights** - Comprehensive performance analysis

### **Coach View**
- 👀 **Read-Only Access** - Separate view for coaches
- 🔄 **Auto-Refresh** - Always shows latest data from Google Sheets
- 📊 **Full Analytics** - All analysis tabs available

### **Mobile & Accessibility**
- 📱 **Mobile-Friendly** - Optimized for iPhone and all devices
- 🎨 **Clean Interface** - No sidebar clutter, focus on data
- 🔗 **Link Previews** - Looks great when shared on social media

## 🚀 Quick Start

### **Files in This Repository**

```
your-repo/
├── streamlit_app.py           # Main application
├── coach_view.py              # Coach-only read-only view
├── requirements.txt           # Python dependencies
├── packages.txt               # System dependencies
├── apt-packages.txt           # Additional system packages
├── preview.png                # Social media preview image
├── .streamlit/
│   └── config.toml           # App configuration
├── README.md                  # This file
├── START_DEPLOYMENT_HERE.md   # Quick deployment guide
└── GOOGLE_SHEETS_SETUP_GUIDE.md  # Cloud setup instructions
```

## 📦 Deployment Steps

### **1. Create GitHub Repository**
1. Create a new GitHub repository
2. Upload all 7 essential files listed above

### **2. Setup Google Sheets (Optional but Recommended)**
1. Follow `GOOGLE_SHEETS_SETUP_GUIDE.md` for detailed instructions
2. Create a Google Cloud service account
3. Share your Google Sheet with the service account email
4. Add credentials to Streamlit Cloud secrets

### **3. Deploy on Streamlit Cloud**
1. Go to https://share.streamlit.io/
2. Connect your GitHub repository
3. Select `streamlit_app.py` as the main file
4. Add Google Sheets credentials to secrets (if using)
5. Deploy!

### **4. Deploy Coach View (Optional)**
1. Create a second app on Streamlit Cloud
2. Same repository, but select `coach_view.py` as main file
3. Use same Google Sheets credentials
4. Share the coach URL with coaches

## 🔧 Technical Details

### **Python Dependencies**
```
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
matplotlib>=3.7.0,<3.9.0
seaborn>=0.12.0
openpyxl>=3.1.0
pytesseract>=0.3.10
Pillow>=10.0.0
gspread>=5.11.0
google-auth>=2.23.0
```

### **System Dependencies**
- tesseract-ocr (for OCR functionality)
- tesseract-ocr-eng
- libtesseract-dev

### **Key Features Implemented**

✅ **Automatic Calculations**
- Total Turns = Left + Right + Back Turns
- Ball Touches = Left + Right Foot Touches
- Left Foot % = (Left Touches / Ball Touches) × 100
- Kicking Power = Max of Left or Right Kicking Power
- Work Rate = (Distance × 1760) / Duration (yards per minute)

✅ **Training Types**
- Speed and Agility (no ball)
- Ball Work (with ball)
- Match-Grass, Match-Turf, Match-Hard (with ball, game stats)

✅ **Smart Form Features**
- Dynamic field visibility based on training type
- Dropdown with custom entry for Session Name, Coach, Location
- Fixed dropdowns for Surface and Intensity
- Confirmation dialog before saving data
- Reset button to clear form

✅ **Match Play Tab**
- Exclusive match-specific metrics: Position, Goals, Assists, Work Rate, Ball Possessions
- Filter by coach and time period
- Select specific match for detailed view
- Surface breakdown analysis

✅ **Mobile Optimizations**
- Responsive layouts
- Touch-friendly buttons
- Charts optimized for mobile
- No sidebar interference

## 📱 Using the App

### **Main App (Data Entry & Full Analytics)**

**Upload & Extract Tab:**
1. Select training type (Speed/Agility, Ball Work, or Match types)
2. Upload training screenshot (optional, OCR extracts data)
3. Fill in form fields (only relevant fields shown per training type)
4. Click "Add to Data File"
5. Confirm to save (auto-syncs to Google Sheets)
6. Form resets for next entry

**Dashboard Tab:**
- View key performance indicators (averages with bests)
- Training summary with recent trends
- Quick insights overview

**Analytics Tab:**
- Select charts from dropdown to view trends
- Filter by coach
- See progress over time

**Speed/Agility/Ball Work Tabs:**
- Dedicated analysis for each training type
- Coach filters
- Time period filters (All Time / Last 30 Days)
- Specific metrics and visualizations

**Match Play Tab:**
- Only shows match training types
- Match-specific KPIs (Position, Goals, Assists, Work Rate, Ball Possessions)
- Filter by coach and time period
- Select specific match for detailed view

**Personal Records Tab:**
- All-time best performances
- Dates when records were set

**AI Insights Tab:**
- Generate comprehensive training analysis
- Performance trends and recommendations
- Action plans and milestone targets

### **Coach View (Read-Only)**

**Access for Coaches:**
- Same tabs as main app (except Upload & Extract)
- No data entry or editing capabilities
- Auto-refreshes from Google Sheets
- Manual refresh button for latest data
- Perfect for sharing with coaches to review progress

### **Mobile Usage (iPhone/Android)**

1. **Open URL** - Navigate to your Streamlit app URL
2. **Add to Home Screen** - For quick access (optional)
3. **Upload Photos** - Take training screenshots and upload
4. **View Analytics** - All charts and metrics work on mobile
5. **Share with Coach** - Send coach view URL to trainers

## 🔑 Google Sheets Setup

### **Why Use Google Sheets?**
- ☁️ Cloud backup of all training data
- 🔄 Automatic sync between apps
- 👥 Easy data sharing with coaches
- 📊 Additional analysis in spreadsheet
- 💾 No data loss even if app resets

### **Setup Steps:**
1. Create a Google Cloud project
2. Enable Google Sheets API
3. Create a service account and download JSON key
4. Share your Google Sheet with service account email
5. Add credentials to Streamlit secrets

**See `GOOGLE_SHEETS_SETUP_GUIDE.md` for detailed instructions!**

## 📊 Data Fields

### **Session Info (All Types)**
- Date, Session Name, Coach, Location, Surface, Training Type, Duration, Intensity

### **Movement Metrics (All Types)**
- Total Distance, Sprint Distance, Top Speed, Number of Sprints, Accelerations/Decelerations

### **Agility (All Types)**
- Left Turns, Right Turns, Back Turns, Intense Turns, Total Turns (calculated)
- Avg Turn Entry Speed, Avg Turn Exit Speed

### **Ball Work (Ball Work + Match Types)**
- Left Foot Touches, Right Foot Touches, Ball Touches (calculated)
- Left Foot % (calculated), Left Releases, Right Releases
- Left Kicking Power, Right Kicking Power, Kicking Power (calculated)

### **Match Stats (Match Types Only)**
- Position, Goals, Assists, Work Rate (calculated), Ball Possessions

## 🎯 Calculated Fields

The app automatically calculates these fields:

1. **Total Turns** = Left Turns + Right Turns + Back Turns
2. **Ball Touches** = Left Foot Touches + Right Foot Touches
3. **Left Foot %** = (Left Foot Touches / Ball Touches) × 100
4. **Kicking Power** = max(Left Kicking Power, Right Kicking Power)
5. **Work Rate** = (Total Distance in miles × 1760) / Duration in minutes (yards/min)

Users cannot manually enter these fields - they're computed automatically to ensure data consistency.

## 🆘 Troubleshooting

### **Common Issues:**

**App won't load:**
- Check all required files are uploaded to GitHub
- Verify `packages.txt` and `apt-packages.txt` are in root directory
- Check Streamlit Cloud deployment logs

**Google Sheets not syncing:**
- Verify service account email has edit access to sheet
- Check credentials are correctly added to Streamlit secrets
- Ensure Google Sheets API is enabled in Google Cloud

**OCR not working:**
- OCR requires `packages.txt` to be properly configured
- The app works fine without OCR - manual entry always available
- Check deployment logs for tesseract installation errors

**Charts not showing:**
- Ensure data is loaded (refresh data button)
- Check filters aren't excluding all data
- Try selecting a different chart from dropdown

**Form not resetting:**
- Click "Reset Form" button
- Form auto-resets after successful save
- Refresh browser if issue persists

## 🔒 Security & Privacy

- Google Sheets credentials stored securely in Streamlit secrets
- Service account has no access to personal Google account
- Coach view is read-only (no editing capabilities)
- All data synced to your private Google Sheet

## 📈 Future Enhancements

Potential features to add:
- Export analytics reports as PDF
- Team comparison views
- Seasonal performance tracking
- Goal setting and progress tracking
- Training load management
- Injury tracking integration

## 📄 License

Personal use project for tracking Mia's soccer training progress.

## 🙏 Acknowledgments

Built with:
- [Streamlit](https://streamlit.io/) - Web app framework
- [Google Sheets API](https://developers.google.com/sheets/api) - Cloud storage
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) - Image text extraction
- [Matplotlib](https://matplotlib.org/) & [Seaborn](https://seaborn.pydata.org/) - Data visualization

---

**Ready to deploy?** Start with `START_DEPLOYMENT_HERE.md` for step-by-step instructions! 🚀
