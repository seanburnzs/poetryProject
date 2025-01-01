document.addEventListener('DOMContentLoaded', function () {
    // Function to get CSRF token from cookies
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const csrftoken = getCookie('csrftoken');

    // Reaction Icons Mapping
    const reactionIcons = {
        'insightful': 'fas fa-lightbulb text-warning',
        'beautiful': 'fas fa-feather text-primary',
        'inspiring': 'fas fa-sun text-success',
        'sad': 'fas fa-sad-tear text-info',
        'funny': 'fas fa-laugh text-warning',
        'thoughtful': 'fas fa-brain text-secondary',
        'uplifting': 'fas fa-smile-beam text-success',
    };

    // Event Delegation for Like and Favorite Buttons
    document.body.addEventListener('click', function (event) {
        // Handle Like Button Click
        const likeButton = event.target.closest('.like-button');
        if (likeButton) {
            event.preventDefault();
            event.stopPropagation(); // Prevent the event from bubbling up

            const poemId = likeButton.getAttribute('data-poem-id');
            if (!poemId) {
                console.error('No poem ID found for like button.');
                return;
            }

            fetch(`/toggle_like_ajax/${poemId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'Content-Type': 'application/json',
                },
            })
                .then(response => response.json())
                .then(data => {
                    const icon = likeButton.querySelector('i');
                    const likeCountSpan = likeButton.parentElement.querySelector('.likes-count');

                    if (data.liked) {
                        icon.classList.remove('far', 'fa-heart', 'text-secondary');
                        icon.classList.add('fas', 'fa-heart', 'text-danger');
                    } else {
                        icon.classList.remove('fas', 'fa-heart', 'text-danger');
                        icon.classList.add('far', 'fa-heart', 'text-secondary');
                    }
                    // set the exact count from server
                    likeCountSpan.textContent = `${data.like_count} Likes`;                    

                    // Add snap animation
                    likeButton.classList.add('snap-animation');
                    setTimeout(function () {
                        likeButton.classList.remove('snap-animation');
                    }, 500);
                })
                .catch((error) => {
                    console.error('Error:', error);
                    alert(`An error occurred while updating your like.`);
                });
        }

        // Handle Favorite Button Click
        const favoriteButton = event.target.closest('.star-button');
        if (favoriteButton) {
            event.preventDefault();
            event.stopPropagation(); // Prevent the event from bubbling up

            const poemId = favoriteButton.getAttribute('data-poem-id');
            if (!poemId) {
                console.error('No poem ID found for favorite button.');
                return;
            }

            fetch(`/toggle_favorite_ajax/${poemId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'Content-Type': 'application/json',
                },
            })
                .then(response => response.json())
                .then(data => {
                    const icon = favoriteButton.querySelector('i');

                    if (data.favorited) {
                        icon.classList.remove('far', 'fa-star', 'text-secondary');
                        icon.classList.add('fas', 'fa-star', 'text-warning');
                    } else {
                        icon.classList.remove('fas', 'fa-star', 'text-warning');
                        icon.classList.add('far', 'fa-star', 'text-secondary');
                    }

                    // Add snap animation
                    favoriteButton.classList.add('snap-animation');
                    setTimeout(function () {
                        favoriteButton.classList.remove('snap-animation');
                    }, 500);
                })
                .catch((error) => {
                    console.error('Error:', error);
                    alert('An error occurred while updating your favorite.');
                });
        }

        // Handle Reaction Button Click
        const reactionButton = event.target.closest('.reaction-button');
        if (reactionButton) {
            event.preventDefault();
            event.stopPropagation(); // Prevent the event from bubbling up

            const poemId = reactionButton.getAttribute('data-poem-id');
            const reactionType = reactionButton.getAttribute('data-reaction-type');
            if (!poemId || !reactionType) {
                console.error('Invalid data attributes for reaction button.');
                return;
            }

            // Ensure 'like' is not handled here
            if (reactionType === 'like') {
                console.warn('Like reaction should be handled via the like button.');
                return;
            }

            fetch(`/poem/${poemId}/add_reaction/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 'reaction_type': reactionType }),
            })
                .then(response => response.json())
                .then(data => {
                    // Update the selected reactions
                    const selectedReactionsContainer = reactionButton.closest('.reaction-container').querySelector('.selected-reactions');
                    selectedReactionsContainer.innerHTML = '';

                    if (data.current_reactions && data.current_reactions.length > 0) {
                        data.current_reactions.forEach(reaction => {
                            if (reaction !== 'like') { // Exclude 'like' if handled separately
                                const iconClass = reactionIcons[reaction];
                                const reactionIcon = document.createElement('i');
                                reactionIcon.className = `${iconClass} reaction-icon`;
                                reactionIcon.title = reaction.charAt(0).toUpperCase() + reaction.slice(1);
                                selectedReactionsContainer.appendChild(reactionIcon);
                            }
                        });
                    }

                    // Hide the reaction menu
                    const reactionMenu = reactionButton.closest('.reaction-menu');
                    reactionMenu.classList.remove('show');
                    reactionMenu.classList.add('hide');
                    setTimeout(() => {
                        reactionMenu.style.display = 'none';
                    }, 200);
                })
                .catch((error) => {
                    console.error('Error:', error);
                    alert('An error occurred while updating your reaction.');
                });
        }

        // Handle Reaction Toggle Button Click
        const reactionToggle = event.target.closest('.reaction-toggle');
        if (reactionToggle) {
            event.preventDefault();
            event.stopPropagation(); // Prevent the event from bubbling up

            const reactionMenu = reactionToggle.parentElement.querySelector('.reaction-menu');

            // Hide all other open reaction menus
            document.querySelectorAll('.reaction-menu.show').forEach(menu => {
                if (menu !== reactionMenu) {
                    menu.classList.remove('show');
                    menu.classList.add('hide');
                    setTimeout(() => {
                        menu.style.display = 'none';
                    }, 200);
                }
            });

            if (reactionMenu.classList.contains('show')) {
                reactionMenu.classList.remove('show');
                reactionMenu.classList.add('hide');
                setTimeout(() => {
                    reactionMenu.style.display = 'none';
                }, 200);
            } else {
                reactionMenu.style.display = 'block';
                setTimeout(() => {
                    reactionMenu.classList.remove('hide');
                    reactionMenu.classList.add('show');
                }, 10);
            }
        }

        // Handle Three Dots Menu Click
        const threeDotsButton = event.target.closest('.three-dots-button');
        if (threeDotsButton) {
            event.preventDefault();
            event.stopPropagation(); // Prevent the event from bubbling up

            const menuContent = threeDotsButton.nextElementSibling;

            // Hide all other visible menus
            document.querySelectorAll('.menu-content.visible').forEach(menu => {
                if (menu !== menuContent) {
                    menu.classList.remove('visible');
                }
            });

            menuContent.classList.toggle('visible');
        }
    });

    // Hide menus when clicking outside
    document.addEventListener('click', function (event) {
        // Hide all menu-content elements
        document.querySelectorAll('.menu-content.visible').forEach(menu => {
            menu.classList.remove('visible');
        });

        // Hide all reaction menus
        document.querySelectorAll('.reaction-menu.show').forEach(menu => {
            menu.classList.remove('show');
            menu.classList.add('hide');
            setTimeout(() => {
                menu.style.display = 'none';
            }, 200);
        });
    });

    // Copy Link Functionality
    window.copyLink = function (url) {
        navigator.clipboard.writeText(url).then(function () {
            alert('Link copied to clipboard!');
        }).catch(function (err) {
            console.error('Failed to copy the link:', err);
            alert('Failed to copy the link.');
        });
    };
});
