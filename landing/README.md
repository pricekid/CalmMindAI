# Dear Teddy Landing Page

This is the static landing page for the Dear Teddy mental wellness application.

## Deployment on Render.com

### Static Site Setup

1. Log in to your Render.com account
2. Click "New" and select "Static Site"
3. Connect your GitHub repository
4. Configure the deployment settings:
   - Name: dearteddy-landing
   - Build Command: (leave empty)
   - Publish Directory: landing

5. Click "Create Static Site"

### Custom Domain Setup (Optional)

1. After deployment, go to the "Settings" tab
2. Scroll to the "Custom Domain" section
3. Click "Add Custom Domain"
4. Follow the instructions to set up DNS records

## File Structure

```
landing/
├── index.html           # Main landing page HTML
├── static/              # Static assets
│   ├── css/             # CSS stylesheets
│   │   └── landing.css  # Main stylesheet
│   ├── js/              # JavaScript files
│   │   └── install.js   # PWA installation script
│   ├── images/          # Image assets
│   └── manifest.json    # PWA manifest file
└── render.yaml          # Render.com configuration
```

## Updating the Landing Page

To update the landing page:

1. Modify the HTML, CSS, or JavaScript files as needed
2. Commit and push your changes to GitHub
3. Render.com will automatically deploy the updates

## Connecting to the Main App

The landing page links to the main Dear Teddy application. Update the following URLs if your application's domain changes:

- Login link
- Registration link
- Any other links to the main application