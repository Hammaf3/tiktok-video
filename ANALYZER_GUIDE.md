# 🔍 YouTube Video Analyzer - Complete Guide

## ✅ Features

### Search Capabilities:
- ✅ Search ANY video type (cooking, tech, comedy, etc.)
- ✅ Filter by country (Pakistan 🇵🇰, UK 🇬🇧, US 🇺🇸, Canada 🇨🇦, Australia 🇦🇺, India 🇮🇳)
- ✅ Get top 20-50 videos
- ✅ Ranked by viral score (0-100)
- ✅ High views, best engagement

### Viral Score Formula:
- Engagement rate (40%)
- Views per day velocity (30%)
- Like ratio (20%)
- Total views (10%)
- Duration bonus (30-90s videos get 1.2x)
- Recency bonus (videos <30 days get 1.3x)

### Display Information:
- Video thumbnail
- Title and channel
- Views, likes, comments
- Duration
- Days since published
- Viral score (0-100)
- Rank (#1, #2, #3...)

---

## 🚀 How to Use

### Step 1: Run Analyzer

```bash
python analyzer_web.py
```

**Output:**
```
============================================================
🔍 YouTube Video Analyzer with Country Filter
============================================================

✅ Search any video type
✅ Filter by country (Pakistan, UK, US, Canada, Australia)
✅ Get top 20-30 videos ranked by viral score
✅ High views, best engagement

Open in browser: http://localhost:5001
============================================================
```

### Step 2: Open Browser

```
http://localhost:5001
```

### Step 3: Search Videos

**Example searches:**
- "cooking recipes"
- "funny videos"
- "tech reviews"
- "gaming highlights"
- "satisfying videos"
- "workout routines"

**Select country:**
- 🇵🇰 Pakistan
- 🇬🇧 United Kingdom
- 🇺🇸 United States
- 🇨🇦 Canada
- 🇦🇺 Australia
- 🇮🇳 India

**Number of videos:** 10-50

### Step 4: View Results

Results show:
- **Rank** (#1 is best)
- **Thumbnail** (click to open on YouTube)
- **Title** and **Channel**
- **Views, Likes, Comments**
- **Duration** and **Age**
- **Viral Score** (0-100)

---

## 💡 Use Cases

### Use Case 1: Find Trending Content
```
Search: "viral moments 2024"
Country: United States
Limit: 30
```
**Result:** Top 30 viral videos from US

### Use Case 2: Local Content Research
```
Search: "pakistani food"
Country: Pakistan
Limit: 25
```
**Result:** Top 25 food videos popular in Pakistan

### Use Case 3: Niche Analysis
```
Search: "tech tutorials"
Country: UK
Limit: 20
```
**Result:** Top 20 tech videos in UK

### Use Case 4: Find TikTok-Ready Videos
```
Search: "short funny clips"
Country: US
Limit: 30
```
**Result:** Videos perfect for TikTok conversion (30-90s get bonus score)

---

## 🎯 Integration with Converter

### Workflow:
1. **Search** for videos using analyzer
2. **Find** best video (highest viral score)
3. **Copy** YouTube URL
4. **Convert** using simple_web_app.py or web_app.py
5. **Upload** to TikTok

### Example:
```bash
# Terminal 1: Run analyzer
python analyzer_web.py
# Open: http://localhost:5001

# Terminal 2: Run converter
python simple_web_app.py
# Open: http://localhost:5000

# Workflow:
# 1. Search in analyzer (port 5001)
# 2. Find best video
# 3. Copy URL
# 4. Paste in converter (port 5000)
# 5. Download converted video
# 6. Upload to TikTok
```

---

## 📊 Understanding Viral Score

### Score Ranges:
- **90-100:** 🔥 Extremely Viral (must convert!)
- **75-89:** 📈 Highly Viral (great choice)
- **60-74:** 💎 Good Engagement (solid pick)
- **40-59:** 📊 Average (consider carefully)
- **0-39:** 📉 Low Engagement (skip)

### What Makes High Score:
- ✅ High views relative to age
- ✅ High engagement (likes + comments)
- ✅ Good like ratio
- ✅ Optimal duration (30-90s)
- ✅ Recent upload (<30 days)

---

## 🌍 Country Filtering

### Why Country Matters:
- Different countries have different trending content
- Local content performs better in that region
- Language and culture preferences
- TikTok audience varies by country

### Best Practices:
- **Pakistan:** Search Urdu/English content
- **UK/US:** English content, similar trends
- **India:** Hindi/English, Bollywood content
- **Canada/Australia:** English, similar to US/UK

---

## 🔧 Requirements

### API Key Needed:
```env
# .env file
YOUTUBE_API_KEY=AIzaSyXXXXXXXXXXXX
```

### Get YouTube API Key:
1. Go to: https://console.cloud.google.com/
2. Create project
3. Enable YouTube Data API v3
4. Create API key
5. Add to .env file

### Free Quota:
- 10,000 units per day
- Each search uses ~100 units
- Can do ~100 searches per day

---

## 💰 Client Value

### What Client Gets:
- ✅ Research tool for viral content
- ✅ Country-specific trending videos
- ✅ Ranked by engagement
- ✅ Perfect for TikTok conversion
- ✅ Save hours of manual research

### Pricing:
- **Research Tool:** $100-200 one-time
- **Monthly Access:** $50/month
- **Combined with Converter:** $300-500 setup

---

## 🎉 Summary

**Analyzer Features:**
- Search any video type ✅
- Filter by 6 countries ✅
- Get 20-50 top videos ✅
- Viral score ranking ✅
- High views, best engagement ✅
- Beautiful web interface ✅

**Perfect for:**
- Content research
- Finding viral videos
- TikTok content planning
- Competitor analysis
- Trend discovery

---

## 🚀 Quick Start

```bash
# 1. Run analyzer
python analyzer_web.py

# 2. Open browser
http://localhost:5001

# 3. Search
Query: "cooking recipes"
Country: Pakistan
Limit: 25

# 4. Click Search

# 5. View top 25 videos ranked by viral score!
```

---

**Ready to find viral videos!** 🔍🔥
