# Video Provider Bot💎

Pyasi Angel is a sophisticated Telegram bot designed to deliver exclusive content to users. It features a premium user system, daily usage limits for free users, a point-based economy, a referral system, and an admin panel for broadcasting messages and managing users.

The bot is built with Python, uses MongoDB for persistent data storage, and is designed for easy deployment on platforms like Koyeb.

 <!-- You can replace this with a link to your own screenshot -->

---

## ✨ Features

-   **Content on Demand**: Serves random video and photo content from a private source channel.
-   **User Tiers**: Supports both `Normal` and `Premium` users.
    -   **Normal Users**: Have a daily limit on the number of videos they can request.
    -   **Premium Users**: Enjoy unlimited access.
-   **Point & Referral System**:
    -   Users earn points for watching videos.
    -   Users get a unique referral link to invite others.
    -   Successful referrals reward the referrer with bonus points.
-   **Leaderboard**: A public leaderboard ranks users based on the number of successful referrals.
-   **Persistent Database**: Uses MongoDB to store all user data, including points, referral counts, and premium status.
-   **Admin Panel**:
    -   `/broadcast`: Send a message to all users of the bot.
    -   `/addpremium <user_id>`: Upgrade a user to premium.
    -   `/removepremium <user_id>`: Downgrade a premium user to normal.

---

## 🛠️ Technology Stack

-   **Language**: Python 3
-   **Library**: `python-telegram-bot`
-   **Database**: MongoDB (via `pymongo`)
-   **Deployment**: Ready for Git-based deployment on platforms like Koyeb.

---

## 🚀 Setup and Deployment

Follow these steps to get your own instance of the bot running.

### 1. Prerequisites

-   **Telegram Bot Token**: Get a token from [@BotFather](https://t.me/BotFather) on Telegram.
-   **MongoDB Atlas Account**: Create a free cluster on [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) and get your database connection string (URI).
-   **Private Source Channel**:
    1.  Create a **private** Telegram channel. This is where you will upload all your videos and photos.
    2.  Add your bot to this channel as an **Administrator**.
    3.  Get the Channel ID. Forward a message from the channel to a bot like `@userinfobot` to get its ID (it will be a negative number, e.g., `-1001234567890`).

### 2. Fork and Clone the Repository

Fork this repository to your own GitHub account and then clone it to your local machine.

### 3. Deployment on Koyeb (Recommended)

This project is optimized for deployment on Koyeb's free tier.

1.  **Create a GitHub Repository**: Push the project files (`bot.py`, `requirements.txt`, `Procfile`) to a new **private** GitHub repository.

2.  **Create a Koyeb App**:
    -   On the Koyeb dashboard, click **"Create App"**.
    -   Connect your GitHub and select the repository for the bot.
    -   **Change Service Type**: In the service configuration, change the type from `Web Service` to **`Worker`**.
    -   **Add Environment Variables**: This is the most critical step. Add the following environment variables with your credentials:
        -   `BOT_TOKEN`: Your token from BotFather.
        -   `MONGO_URI`: Your MongoDB connection string.
        -   `DATABASE_NAME`: The name of your database (e.g., `pyasi-bot-db`).
        -   `SOURCE_CHANNEL_ID`: The ID of your private content channel.
        -   `ADMIN_IDS`: A comma-separated list of your numeric Telegram user IDs (e.g., `11111111,22222222`).

3.  **Deploy**: Click **"Deploy"**. Koyeb will automatically build and run your bot. You can monitor the logs from the Koyeb dashboard.

---

## 🤖 Bot Commands

### User Commands

-   `/start`: Initializes the bot, registers the user, and shows the main menu.
-   **(Buttons)**: All other user interactions (getting videos/photos, checking points, etc.) are handled via inline buttons.

### Admin Commands

-   `/broadcast <message>`: Sends a text message to every user who has ever started the bot.
-   `/addpremium <user_id>`: Grants a user unlimited access.
-   `/removepremium <user_id>`: Revokes a user's premium status.

---

## 📁 Project Structure
