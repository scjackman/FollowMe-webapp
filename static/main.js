// Utility function to get a cookie value by name
// Returns the value of the cookie if found, otherwise undefined
function getCookie(name) {
    // Prepend a semicolon and space to ensure we match the cookie name exactly
    const value = `; ${document.cookie}`;
    // Split the cookie string at the target cookie name
    const parts = value.split(`; ${name}=`);
    // If the cookie exists, split at the next semicolon to get its value
    if (parts.length === 2) return parts.pop().split(';').shift();
    // If not found, returns undefined
}

// Wait for the DOM to be fully loaded before running the script
window.addEventListener('DOMContentLoaded', async () => {
    // Try to get the userID cookie
    const userId = getCookie('userID');
    // Get references to the form and main content sections
    const createUserForm = document.getElementById('create-user-form');
    const mainContent = document.getElementById('main-content');

    if (userId) {
        // If a userID cookie exists, the user is recognized
        // Hide the user creation form
        createUserForm.style.display = 'none';
        // Show the main app content
        mainContent.style.display = '';
        // Load user info and the feed from the backend
        await loadUserInfo();
    } else {
        // If no userID cookie, the user is new or not recognized
        // Show the user creation form
        createUserForm.style.display = '';
        // Hide the main app content
        mainContent.style.display = 'none';

        // Show the alert after a short delay to allow rendering
        setTimeout(() => {
            alert("Notice: This site remembers you using a simple cookie. No sensitive data is stored.");
        }, 1 );
    }
});

// Handle user creation form submission
const createUserForm = document.getElementById('create-user-form');
if (createUserForm) {
    createUserForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const nickname = document.getElementById('nickname').value.trim();
        const origin = document.getElementById('origin').value.trim();
        if (!nickname || !origin) return;
        try {
            const res = await fetch('/api/create_user', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ nickname, origin })
            });
            if (res.ok) {
                // On success, reload the page to show main content
                window.location.reload();
            } else {
                const data = await res.json();
                alert(data.error || 'Failed to create user.');
            }
        } catch (err) {
            alert('Network error. Please try again.');
        }
    });
}

// Global variables for pagination
let currentPage = 1;
let hasMoreUsers = true;

// Load user information and display it
async function loadUserInfo() {
    try {
        console.log('Loading user info...');
        const response = await fetch('/api/user_info');
        console.log('Response status:', response.status);
        
        if (response.ok) {
            const userData = await response.json();
            console.log('User data:', userData);
            document.getElementById('user-nickname').textContent = userData.nickname;
            
            await loadUsersFeed();
        } else {
            console.log('User not found, showing creation form');
            // If user not found, show creation form
            document.getElementById('create-user-form').style.display = '';
            document.getElementById('main-content').style.display = 'none';
        }
    } catch (error) {
        console.error('Error loading user info:', error);
    }
}

// Load and display the users feed
async function loadUsersFeed(page = 1) {
    try {
        const response = await fetch(`/api/users_feed?page=${page}`);
        if (response.ok) {
            const data = await response.json();
            renderUsersFeed(data.users, page === 1);
            hasMoreUsers = data.hasMore;
            currentPage = data.page;
            
            // Show/hide load more button
            const loadMoreBtn = document.getElementById('load-more');
            loadMoreBtn.style.display = hasMoreUsers ? 'block' : 'none';
        }
    } catch (error) {
        console.error('Error loading users feed:', error);
    }
}

// Render the users feed
function renderUsersFeed(users, clearExisting = false) {
    const feedContainer = document.getElementById('users-feed');
    
    if (clearExisting) {
        feedContainer.innerHTML = '';
    }
    
    users.forEach(user => {
        const userCard = document.createElement('div');
        userCard.className = 'user-card';
        userCard.innerHTML = `
            <div>
                <strong>${user.nickname}</strong>
                <br>
                <small>${user.origin || 'Unknown origin'}</small>
            </div>
            <button 
                class="follow-btn" 
                data-user-id="${user.userID}"
                ${user.isFollowing ? 'disabled' : ''}
            >
                ${user.isFollowing ? 'Following' : 'Follow'}
            </button>
        `;
        feedContainer.appendChild(userCard);
    });
    
    // Add event listeners to follow buttons
    addFollowButtonListeners();
}

// Add event listeners to follow buttons
function addFollowButtonListeners() {
    document.querySelectorAll('.follow-btn').forEach(button => {
        button.addEventListener('click', async (e) => {
            const targetUserId = e.target.dataset.userId;
            if (e.target.disabled) return;
            
            try {
                const response = await fetch('/api/follow_user', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ targetUserID: targetUserId })
                });
                
                if (response.ok) {
                    // Update button state
                    e.target.disabled = true;
                    e.target.textContent = 'Following';
                    
                    // Reload following list and feed to reflect changes
                    await loadUserInfo();
                } else {
                    const data = await response.json();
                    alert(data.error || 'Failed to follow user');
                }
            } catch (error) {
                alert('Network error. Please try again.');
            }
        });
    });
}

// Load more users (by pagination)
async function loadMoreUsers() {
    if (hasMoreUsers) {
        await loadUsersFeed(currentPage + 1);
    }
}

// Add event listener for load more button
document.addEventListener('DOMContentLoaded', () => {
    const loadMoreBtn = document.getElementById('load-more');
    if (loadMoreBtn) {
        loadMoreBtn.addEventListener('click', loadMoreUsers);
    }
}); 