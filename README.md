# Poetry Sharing Project
> A Django-based social media platform for sharing poetry. Create an account, post poems, engage with others via likes, comments, and favorites, and explore new content through a discover feed.

---

## Features
- **User Authentication**  
  Sign up, log in, and manage profiles with custom bios and profile pictures stored on AWS S3.
- **Poem Management**  
  Submit, edit, view, and organize poems into user-defined folders.
- **Engagement**  
  Like, favorite, and comment on poetry.
- **Messaging**  
  Start conversations and exchange direct messages with other users.
- **Search & Discovery**  
  Find poems or users, explore trending content, and follow other poets.
- **Notifications**  
  Get real-time alerts for new followers, poem interactions, and messages.

---

## Tech Stack
- **Django**: Core framework for models, views, and templates  
- **Supabase PostgreSQL**: Hosted relational database  
- **AWS S3**: Storage for user profile images  
- **Render**: Platform for deployment  
- **HTML, CSS, JavaScript**: Front-end styling and interactivity  
- **Poetrydb.org**: Fetch Poems
   > *Example: https://poetrydb.org/author/Shakespeare*

---

## Usage
1. **Register or Log In** to create your profile.  
2. **Submit Poetry** or discover new work on the homepage.  
3. **Engage** with poems—like, comment, favorite, or add to custom folders.  
4. **Follow Users** to see their poetry in your feed.  
5. **Direct Message** others to start or continue conversations.  
   > *Note: Direct messaging is currently disabled on the live build.*

---

## Contributing
Contributions are welcome. Feel free to open issues or submit pull requests to enhance features, fix bugs, or improve documentation.

## DISCLAIMER
The site is deployed on Render and is technically in production, so it will shutdown after inactivity, meaning when you first load the site, it will take one minute.

## Known Bug  
- Friends Tab doesn't populate sometimes  
- Profile pictures sometimes go to the wrong AWS S3 URL  

## Tester Creds  
**U:** tester  
**PW:** observer 