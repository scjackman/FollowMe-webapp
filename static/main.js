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
    const privateUserID = getCookie('privateUserID');
    // Get references to the form and main content sections
    const createUserForm = document.getElementById('create-user-form');
    const mainContent = document.getElementById('main-content');

    if (privateUserID) {
        // If a privateUserID cookie exists, the user is recognized
        // Hide the user creation form
        createUserForm.style.display = 'none';
        // Show the main app content
        mainContent.style.display = '';
        // Load user info and the feed from the backend
        await loadUserInfo();
    } else {
        // If no privateUserID cookie, the user is new or not recognized
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
    const spinner = document.getElementById(page === 1 ? 'spinner' : 'load-more-spinner');
    if (spinner) spinner.style.display = 'block';
    try {
        const response = await fetch(`/api/users_feed?page=${page}`);
        if (response.ok) {
            const data = await response.json();
            renderUsersFeed(data.users, page === 1);
            hasMoreUsers = data.hasMore;
            currentPage = data.page;
        }
    } catch (error) {
        console.error('Error loading users feed:', error);
    } finally {
        if (spinner) spinner.style.display = 'none';
    }
}

// Render the users feed
function renderUsersFeed(users, clearExisting = false) {
    const feedContainer = document.querySelector('.users-list');
    if (!feedContainer) return;

    if (clearExisting) {
        // Clear only the user cards container, not the entire feed container
        const userCardsContainer = document.getElementById('user-cards-container');
        if (userCardsContainer) {
            userCardsContainer.innerHTML = '';
        }
    }
    
    users.forEach(user => {
        const userCard = document.createElement('div');
        let formattedTimeStamp = formatTimestampUserCreatedAt(user)
        
        userCard.className = 'user-card';
        userCard.innerHTML = `
            <div style="display: flex; align-items: center; flex: 1;">
                <div style="width: 48px; height: 48px; border-radius: 50%; background: #e0e0e0; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; color: #888; margin-right: 1rem; flex-shrink: 0;">
                    <span style="user-select: none;">👤</span>
                </div>
                <div style="display: flex; flex-direction: column;">
                    <strong>${user.nickname}</strong>
                    <small>
                        ${user.origin || 'Unknown origin'}
                        <span style="font-size: 0.8em;">•</span>
                        ${formattedTimeStamp}
                    </small>
                    <small>Followers: ${user.followerCount}</small>
                </div>
            </div>
            <button 
                class="btn btn-outline-secondary btn-sm follow-btn" 
                data-user-id="${user.publicUserID}"
                ${user.isFollowing ? 'disabled' : ''}
            >
                ${user.isFollowing ? 'Following' : 'Follow'}
            </button>
        `;
        
        // Append to the user cards container instead of the feed container
        const userCardsContainer = document.getElementById('user-cards-container');
        if (userCardsContainer) {
            userCardsContainer.appendChild(userCard);
        }
    });
    
    // Add event listeners to follow buttons
    addFollowButtonListeners();
}

// Add event listeners to follow buttons
function addFollowButtonListeners() {
    document.querySelectorAll('.follow-btn').forEach(button => {
        button.addEventListener('click', async (e) => {
            const targetUserID = e.target.dataset.userId;
            if (e.target.disabled) return;

            // Find the follower count element in the same user card
            const userCard = e.target.closest('.user-card');
            const followerCountElem = userCard.querySelector('small:nth-child(3)');
            // Extract the current follower count from the text
            let followerCount = 0;
            if (followerCountElem) {
                const match = followerCountElem.textContent.match(/Followers: (\d+)/);
                if (match) followerCount = parseInt(match[1], 10);
            }

            // Save previous state
            const prevButtonText = e.target.textContent;
            const prevDisabled = e.target.disabled;
            const prevFollowerCount = followerCount;

            // Optimistically update UI
            e.target.disabled = true;
            e.target.textContent = 'Following';
            if (followerCountElem) {
                followerCountElem.textContent = `Followers: ${followerCount + 1}`;
            }

            try {
                const response = await fetch('/api/follow_user', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ targetPublicUserID: targetUserID })
                });

                if (!response.ok) {
                    // Revert UI on error
                    e.target.disabled = prevDisabled;
                    e.target.textContent = prevButtonText;
                    if (followerCountElem) {
                        followerCountElem.textContent = `Followers: ${prevFollowerCount}`;
                    }
                    const data = await response.json();
                    alert(data.error || 'Failed to follow user');
                } else {
                    // Optionally, reload user info/feed if you want to sync with backend
                    // await loadUserInfo();
                }
            } catch (error) {
                // Revert UI on network error
                e.target.disabled = prevDisabled;
                e.target.textContent = prevButtonText;
                if (followerCountElem) {
                    followerCountElem.textContent = `Followers: ${prevFollowerCount}`;
                }
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

// Check if user has scrolled to bottom of the feed
function isNearBottom() {
    const usersList = document.querySelector('.users-list');
    if (!usersList) return false;
    
    const scrollTop = usersList.scrollTop;
    const scrollHeight = usersList.scrollHeight;
    const clientHeight = usersList.clientHeight;
    
    // Load more when user is within 100px of the bottom
    return (scrollTop + clientHeight) >= (scrollHeight - 100);
}

// Handle scroll events for infinite scroll
function handleScroll() {
    if (isNearBottom() && hasMoreUsers && !isLoading) {
        loadMoreUsers();
    }
}

// Track loading state to prevent multiple simultaneous requests
let isLoading = false;

// Load more users (by pagination) with loading state
async function loadMoreUsers() {
    if (hasMoreUsers && !isLoading) {
        isLoading = true;
        await loadUsersFeed(currentPage + 1);
        isLoading = false;
    }
}

// Add scroll event listener for infinite scroll
document.addEventListener('DOMContentLoaded', () => {
    const usersList = document.querySelector('.users-list');
    if (usersList) {
        usersList.addEventListener('scroll', handleScroll);
    }
}); 

// Helper to format timestamp
function formatTimestampUserCreatedAt(user) {
    if (user.createdAt) {
        const date = new Date(user.createdAt);
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = String(date.getFullYear()).slice(-2);
        return `${day}/${month}/${year}`;
    }    
    return '01/01/99'
}