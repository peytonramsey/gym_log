# GymLog - Workout Tracking App

A mobile-responsive web app for tracking your gym workouts, built with Python Flask.

## Features

- **Log Workouts**: Track exercises with sets, reps, weight, and rest time
- **Rest Timer**: Built-in timer to track rest periods between sets
- **Body Metrics**: Log and track your weight and height over time
- **Progress Charts**: Visualize your strength progression over time
- **Calendar View**: See your workout history in a calendar format
- **Workout History**: View detailed history of all your workouts
- **Mobile-Responsive**: Works great on phones, tablets, and desktops

## Installation

1. Install the required dependencies:
```bash
cd gymlog
pip install -r requirements.txt
```

2. Run the app:
```bash
python app.py
```

3. Open your browser and go to:
```
http://localhost:5000
```

## Using on Your Phone

### Option 1: Same WiFi Network
If your phone and computer are on the same WiFi network:

1. Find your computer's IP address:
   - Windows: Run `ipconfig` in Command Prompt, look for IPv4 Address
   - Mac/Linux: Run `ifconfig` or `ip addr`

2. On your phone's browser, go to:
```
http://YOUR_IP_ADDRESS:5000
```
(Replace YOUR_IP_ADDRESS with your actual IP, e.g., http://192.168.1.100:5000)

### Option 2: Deploy Online (Free Options)
- **Render** (https://render.com) - Free tier available
- **PythonAnywhere** (https://pythonanywhere.com) - Free tier available
- **Railway** (https://railway.app) - Free tier available

## How to Use

1. **Home Page**: Quick access to all features
2. **Log Workout**: Add exercises with sets, reps, weight, and rest time
3. **Rest Timer**: Click "Start Rest Timer" on any exercise to use the timer
4. **Body Metrics**: Track your weight and height over time
5. **History**: View all your past workouts
6. **Calendar**: See which days you worked out
7. **Progress**: Select an exercise to see strength progression charts

## Database

The app uses SQLite (gymlog.db) to store all your data locally. The database file will be created automatically when you first run the app.

## Tips

- The app is designed to work on mobile browsers
- Add it to your phone's home screen for an app-like experience
- All data is stored locally in the database
- Back up your gymlog.db file to keep your data safe

## Customization

- Edit the weight units in templates (currently set to lbs)
- Modify rest timer defaults in log.html
- Change color scheme in base.html
