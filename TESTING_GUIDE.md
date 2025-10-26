# Testing Smart Break Scheduling - Step-by-Step Guide

## 🧪 Quick Test Scenarios

### Test 1: Long Haul Route with Morning Departure
**Purpose**: See strategic breaks during sunrise high-risk period

**Steps**:
1. **Origin**: New Orleans, LA (or type "New Orleans")
2. **Destination**: Santa Clara, CA (or type "Santa Clara University")
3. **Departure Time**: 
   - Check "Use Departure Time"
   - Select tomorrow's date
   - Set time to 6:00 AM
4. Click "Optimize Route with Driver Schedule"

**Expected Results**:
- ⭐ Look for **purple-highlighted** breaks with "Strategic" badge
- Morning breaks should overlap with sunrise (high sun glare risk)
- Check if breaks marked as "optimized for high-risk period"
- Safety score should be 85+

---

### Test 2: Cross-Country Route with Afternoon Start
**Purpose**: Test sunset optimization and 10-hour rest scheduling

**Steps**:
1. **Origin**: Los Angeles, CA
2. **Destination**: New York, NY
3. **Departure Time**:
   - Check "Use Departure Time"
   - Select tomorrow's date
   - Set time to 3:00 PM
4. Click "Optimize Route with Driver Schedule"

**Expected Results**:
- Multiple rest stops (10-hour rests) required
- At least one rest stop should be **optimized** (purple badge)
- Evening breaks should align with sunset risk periods
- Total elapsed time should be optimized vs non-optimized schedule

---

### Test 3: East-West Route (Maximum Sun Exposure)
**Purpose**: Maximum sunlight risk - driving directly into/away from sun

**Steps**:
1. **Origin**: San Francisco, CA
2. **Destination**: Las Vegas, NV
3. **Departure Time**:
   - Check "Use Departure Time"  
   - Select tomorrow's date
   - Set time to 7:00 AM (sunrise direction)
4. Click "Optimize Route with Driver Schedule"

**Expected Results**:
- High sunlight risk scores (70+) in segments
- Early morning break should be **Strategic** (purple)
- Break reason should mention "high-risk period"
- Safety waits may be converted to strategic breaks

---

### Test 4: Short Route (No Optimization Needed)
**Purpose**: Verify system doesn't over-optimize short trips

**Steps**:
1. **Origin**: San Jose, CA
2. **Destination**: San Francisco, CA
3. **No departure time** (use defaults)
4. Click "Optimize Route with Driver Schedule"

**Expected Results**:
- No breaks needed (trip < 8 hours)
- Schedule shows direct route
- No purple "Strategic" badges (not needed)
- Clean, simple schedule

---

## 🔍 What to Look For

### UI Indicators
✅ **Regular Break** - White background, standard reason
```
☕ Rest Stop
2:00 PM - 30 min
FMCSA required 30-minute break after 8 hours driving
```

✅ **Optimized Strategic Break** - Purple background, special badge
```
☕ Rest Stop                    ⭐ Strategic
11:30 AM - 30 min
Strategic break during high-risk period (risk: 75)
```

### Schedule Quality Metrics
- **Safety Score**: Should be 85+ for optimized schedules
- **Total Elapsed Time**: Should be ≤ sum of (driving + breaks + waits)
- **HOS Compliant**: Should always show ✅ True
- **Meets Deadline**: Check if optimized schedule meets your target arrival

### Break/Rest Stop Details
- **Type**: 30_min_break, 10_hour_rest, or safety_wait
- **Optimized Flag**: Shows purple if true
- **Reason**: Explains why stop is needed
- **Risk Score**: Shows sunlight risk if applicable
- **Duration**: 30 min for breaks, 10 hours (600 min) for rest

---

## 🐛 Troubleshooting

### No "Strategic" Breaks Appearing
**Possible Causes**:
1. Route too short (< 8 hours) - no breaks needed
2. Departure time doesn't align with high-risk periods
3. Try morning (6-9 AM) or evening (4-7 PM) departure times

**Solution**: Use longer routes (8+ hours) with early morning or late afternoon departure

### All Breaks Look the Same
**Check**:
- Did you select a departure time? (Calendar integration required)
- Is route long enough to require multiple breaks?
- Try routes that cross multiple time zones

### Schedule Takes Long to Calculate
**Normal Behavior**: 
- Complex routes with many segments take 3-5 seconds
- System is calculating sun position for each segment
- Wait for blue "Optimizing driver schedule..." message to clear

---

## 📊 Validation Checklist

After running a test, verify:

- [ ] **Driver Schedule section appears** (blue box)
- [ ] **Departure and arrival times shown**
- [ ] **Total driving time calculated**
- [ ] **Safety score displayed** (0-100)
- [ ] **HOS compliant status** (should be ✅ True)
- [ ] **At least one break/rest if route > 8 hours**
- [ ] **Purple highlighting on optimized breaks** (long routes)
- [ ] **⭐ Strategic or ⭐ Optimized badge** visible
- [ ] **Warnings section shows optimization notices**

---

## 💡 Pro Tips

1. **Best Times to Test**: 6-9 AM or 4-7 PM departures show most optimization
2. **Long Routes**: 10+ hour routes show multiple strategic breaks
3. **Direction Matters**: East-West routes have higher sun exposure
4. **Check Warnings**: Optimization details appear in warning messages
5. **Compare Safety Scores**: Longer routes with optimization score higher

---

## 🎯 Success Criteria

A successful test shows:
1. ✅ At least one purple-highlighted "Strategic" break
2. ✅ Safety score improves with optimization
3. ✅ Total elapsed time is reasonable (not excessive waits)
4. ✅ All HOS regulations still enforced
5. ✅ Clear explanation of why breaks are optimized

---

**Happy Testing!** 🚀

If you see purple "⭐ Strategic" badges on long-haul routes with morning/evening departures, the feature is working perfectly!
