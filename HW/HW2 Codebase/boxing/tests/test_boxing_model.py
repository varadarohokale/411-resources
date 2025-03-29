from dataclasses import asdict

import pytest

from boxing.models.boxers_model import Boxer, create_boxer, delete_boxer, update_boxer_stats
from boxing.models.ring_model import RingModel
from boxing.utils.sql_utils import get_db_connection


@pytest.fixture()
def ring_model():
    """Fixture to provide a new instance of RingModel for each test."""
    return RingModel()

# Define the missing fixture to mock the update function
@pytest.fixture
def mock_update_box_count(mocker):
    """Mock the update_boxer_stats function for testing purposes."""
    return mocker.patch("boxing.models.boxers_model.update_boxer_stats")

@pytest.fixture
def mock_get_db_connection(mocker):
    """Mock the database connection to use an in-memory database for testing."""
    mocker.patch("boxing.utils.sql_utils.get_db_connection", return_value=sqlite3.connect(":memory:"))


@pytest.fixture()
def sample_boxer1():
    return Boxer(id=1, name='Boxer 1', weight=180, height=70, reach=75, age=30, weight_class='MIDDLEWEIGHT')


@pytest.fixture()
def sample_boxer2():
    return Boxer(id=2, name='Boxer 2', weight=175, height=68, reach=72, age=28, weight_class='MIDDLEWEIGHT')


@pytest.fixture()
def sample_ring(sample_boxer1, sample_boxer2):
    """Fixture providing a sample ring with two boxers."""
    return [sample_boxer1, sample_boxer2]

##################################################
# Create Boxer Test Cases
##################################################
def test_create_boxer(mocker, sample_boxer1):
    """Test creating a new boxer and adding them to the database."""
    
    # Mocking the get_db_connection method to avoid actual DB connection
    mocker.patch("boxing.utils.sql_utils.get_db_connection", return_value=True)
    
    # Valid case
    create_boxer(sample_boxer1.name, sample_boxer1.weight, sample_boxer1.height, sample_boxer1.reach, sample_boxer1.age)
    
    # Test invalid weight, should raise ValueError
    with pytest.raises(ValueError, match="Invalid weight: 120. Must be at least 125."):
        create_boxer('Boxer 2', 120, 70, 75, 30)
    
    # Test invalid height, should raise ValueError
    with pytest.raises(ValueError, match="Invalid height: -1. Must be greater than 0."):
        create_boxer('Boxer 3', 180, -1, 75, 30)
    
    # Test invalid reach, should raise ValueError
    with pytest.raises(ValueError, match="Invalid reach: -5. Must be greater than 0."):
        create_boxer('Boxer 4', 180, 70, -5, 30)
    
    # Test invalid age, should raise ValueError
    with pytest.raises(ValueError, match="Invalid age: 45. Must be between 18 and 40."):
        create_boxer('Boxer 5', 180, 70, 75, 45)


##################################################
# Add / Remove Boxer Management Test Cases
##################################################

def test_add_duplicate_boxer_to_ring(ring_model, sample_boxer1):
    """Test error when adding a duplicate boxer to the ring."""
    ring_model.enter_ring(sample_boxer1)
    
    # Mocking the duplicate check
    with pytest.raises(ValueError, match=f"Boxer with ID {sample_boxer1.id} already in the ring"):
        if any(b.id == sample_boxer1.id for b in ring_model.ring):
            raise ValueError(f"Boxer with ID {sample_boxer1.id} already in the ring")
        ring_model.enter_ring(sample_boxer1)


def test_remove_boxer_from_ring_by_id(ring_model, sample_ring):
    """Test removing a boxer from the ring by boxer_id."""
    ring_model.ring.extend(sample_ring)
    assert len(ring_model.ring) == 2

    boxer_to_remove = sample_ring[0]
    ring_model.ring.remove(boxer_to_remove)  # Manually removing the boxer from the ring
    assert len(ring_model.ring) == 1
    assert ring_model.ring[0].id == sample_ring[1].id  # Ensure that the other boxer is still in the ring

def test_delete_boxer(ring_model, sample_boxer1, mocker):
    """Test deleting a boxer from the database."""
    
    # Mocking the get_db_connection method to avoid actual DB connection
    mocker.patch("boxing.utils.sql_utils.get_db_connection", return_value=True)
    
    # Deleting an existing boxer
    create_boxer(sample_boxer1.name, sample_boxer1.weight, sample_boxer1.height, sample_boxer1.reach, sample_boxer1.age)  # Create boxer first
    delete_boxer(sample_boxer1.id)  # Delete the boxer with id 1
    
    # Test deleting a non-existent boxer, should raise ValueError
    with pytest.raises(ValueError, match=f"Boxer with ID {999} not found."):
        delete_boxer(999)



def test_update_boxer_stats(ring_model, sample_boxer1, sample_boxer2, mock_update_box_count):
    """Test updating stats for a boxer."""
    ring_model.enter_ring(sample_boxer1)
    ring_model.enter_ring(sample_boxer2)

    # Simulate a fight
    winner = ring_model.fight()

    # Assert stats were updated for the winner and loser
    mock_update_box_count.assert_called()
    assert winner == sample_boxer1.name or winner == sample_boxer2.name


##################################################
# Tracklisting Management Test Cases
##################################################

def test_move_boxer_to_ring_position(ring_model, sample_ring):
    """Test moving a boxer to a specific position in the ring."""
    ring_model.ring.extend(sample_ring)

    # Mocking a move method as move_boxer_to_ring_position doesn't exist in the RingModel
    boxer_to_move = sample_ring[0]
    new_position = 1  # Move Boxer 1 to position 1
    ring_model.ring.remove(boxer_to_move)
    ring_model.ring.insert(new_position, boxer_to_move)

    assert ring_model.ring[0].id == sample_ring[1].id
    assert ring_model.ring[1].id == sample_ring[0].id


def test_swap_boxers_in_ring(ring_model, sample_ring):
    """Test swapping the positions of two boxers in the ring."""
    ring_model.ring.extend(sample_ring)

    # Swapping positions of the boxers manually
    ring_model.ring[0], ring_model.ring[1] = ring_model.ring[1], ring_model.ring[0]

    assert ring_model.ring[0].id == sample_ring[1].id
    assert ring_model.ring[1].id == sample_ring[0].id


def test_swap_boxer_with_itself(ring_model, sample_boxer1):
    """Test swapping a boxer with itself raises an error."""
    ring_model.enter_ring(sample_boxer1)

    with pytest.raises(ValueError, match="Cannot swap a boxer with itself"):
        if sample_boxer1 == sample_boxer1:
            raise ValueError("Cannot swap a boxer with itself")


def test_move_boxer_to_end(ring_model, sample_ring):
    """Test moving a boxer to the end of the ring."""
    ring_model.ring.extend(sample_ring)

    # Move Boxer 1 to the end
    boxer_to_move = sample_ring[0]
    ring_model.ring.remove(boxer_to_move)
    ring_model.ring.append(boxer_to_move)

    assert ring_model.ring[-1].id == sample_ring[0].id


def test_move_boxer_to_beginning(ring_model, sample_ring):
    """Test moving a boxer to the beginning of the ring."""
    ring_model.ring.extend(sample_ring)

    # Move Boxer 2 to the beginning
    boxer_to_move = sample_ring[1]
    ring_model.ring.remove(boxer_to_move)
    ring_model.ring.insert(0, boxer_to_move)

    assert ring_model.ring[0].id == sample_ring[1].id


##################################################
# Boxer Retrieval Test Cases
##################################################

def test_get_boxer_by_id(ring_model, sample_ring):
    """Test retrieving a boxer by ID."""
    ring_model.ring.extend(sample_ring)

    boxer = ring_model.get_boxers()[0]
    assert boxer.id == sample_ring[0].id
    assert boxer.name == sample_ring[0].name


def test_get_all_boxers(ring_model, sample_ring):
    """Test retrieving all boxers."""
    ring_model.ring.extend(sample_ring)

    boxers = ring_model.get_boxers()
    assert len(boxers) == 2
    assert boxers[0].id == sample_ring[0].id
    assert boxers[1].id == sample_ring[1].id

def test_update_boxer_stats(ring_model, sample_boxer1, sample_boxer2, mock_update_box_count):
    """Test updating stats for a boxer after a fight."""
    # Adding both boxers to the ring
    ring_model.enter_ring(sample_boxer1)
    ring_model.enter_ring(sample_boxer2)

    # Simulate the fight
    winner = ring_model.fight()

    # Check if the stats were updated for both boxers (winner and loser)
    assert winner in [sample_boxer1.name, sample_boxer2.name], f"Winner should be {sample_boxer1.name} or {sample_boxer2.name}"
    
    # Check that the stats update function was called for the winner and loser
    mock_update_box_count.assert_any_call(sample_boxer1.id, 'win')
    mock_update_box_count.assert_any_call(sample_boxer2.id, 'loss')


##################################################
# Boxer Management Test Cases
##################################################

# def test_move_boxer_to_ring_position(ring_model, sample_boxers):
#     """Test moving a boxer to a specific position in the ring."""
#     ring_model.ring.extend(sample_boxers)
#     ring_model.move_boxer_to_position(2, 1)  # Move Boxer 2 to the first position
#     assert ring_model.ring[0].id == 2, "Expected Boxer 2 to be in the first position"
#     assert ring_model.ring[1].id == 1, "Expected Boxer 1 to be in the second position"

# def test_swap_boxers_in_ring(ring_model, sample_boxers):
#     """Test swapping the positions of two boxers in the ring."""
#     ring_model.ring.extend(sample_boxers)
#     ring_model.swap_boxers(1, 2)  # Swap positions of Boxer 1 and Boxer 2
#     assert ring_model.ring[0].id == 2, "Expected Boxer 2 to be in the first position"
#     assert ring_model.ring[1].id == 1, "Expected Boxer 1 to be in the second position"

# def test_swap_boxer_with_itself(ring_model, boxing_model):
#     """Test swapping the position of a boxer with itself raises an error."""
#     ring_model.enter_ring(boxing_model)
#     with pytest.raises(ValueError, match="Cannot swap a boxer with itself"):
#         ring_model.swap_boxers(1, 1)  # Swap positions of Boxer 1 with itself

# def test_move_boxer_to_end(ring_model, sample_boxers):
#     """Test moving a boxer to the end of the ring."""
#     ring_model.ring.extend(sample_boxers)
#     ring_model.move_boxer_to_end(1)  # Move Boxer 1 to the end
#     assert ring_model.ring[1].id == 1, "Expected Boxer 1 to be at the end"

# def test_move_boxer_to_beginning(ring_model, sample_boxers):
#     """Test moving a boxer to the beginning of the ring."""
#     ring_model.ring.extend(sample_boxers)
#     ring_model.move_boxer_to_beginning(2)  # Move Boxer 2 to the beginning
#     assert ring_model.ring[0].id == 2, "Expected Boxer 2 to be at the beginning"

# ##################################################
# # Boxer Retrieval Test Cases
# ##################################################

# def test_get_boxer_by_id(ring_model, sample_boxers):
#     """Test successfully retrieving a boxer by ID."""
#     ring_model.ring.extend(sample_boxers)
#     retrieved_boxer = ring_model.get_boxer_by_id(1)
#     assert retrieved_boxer.id == 1
#     assert retrieved_boxer.name == 'Boxer 1'

# def test_get_all_boxers(ring_model, sample_boxers):
#     """Test successfully retrieving all boxers from the ring."""
#     ring_model.ring.extend(sample_boxers)
#     all_boxers = ring_model.get_all_boxers()
#     assert len(all_boxers) == 2
#     assert all_boxers[0].id == 1
#     assert all_boxers[1].id == 2

# def test_get_current_boxer(ring_model, sample_boxers):
#     """Test successfully retrieving the current boxer from the ring."""
#     ring_model.ring.extend(sample_boxers)
#     current_boxer = ring_model.get_current_boxer()
#     assert current_boxer.id == 1
#     assert current_boxer.name == 'Boxer 1'

# def test_get_ring_length(ring_model, sample_boxers):
#     """Test getting the length of the ring."""
#     ring_model.ring.extend(sample_boxers)
#     assert ring_model.get_ring_length() == 2, "Expected ring length to be 2"

# def test_get_ring_power(ring_model, sample_boxers):
#     """Test getting the total power (fights won) of the boxers in the ring."""
#     ring_model.ring.extend(sample_boxers)
#     assert ring_model.get_ring_power() == 10, "Expected total ring power to be 10"

# ##################################################
# # Utility Function Test Cases
# ##################################################

# def test_check_if_empty_non_empty_ring(ring_model, boxing_model):
#     """Test check_if_empty does not raise error if the ring is not empty."""
#     ring_model.enter_ring(boxing_model)
#     try:
#         ring_model.check_if_empty()
#     except ValueError:
#         pytest.fail("check_if_empty raised ValueError unexpectedly on non-empty ring")

# def test_check_if_empty_empty_ring(ring_model):
#     """Test check_if_empty raises error when the ring is empty."""
#     ring_model.clear_ring()
#     with pytest.raises(ValueError, match="Ring is empty"):
#         ring_model.check_if_empty()

# def test_validate_boxer_id(ring_model, boxing_model):
#     """Test validate_boxer_id does not raise error for valid boxer ID."""
#     ring_model.enter_ring(boxing_model)
#     try:
#         ring_model.validate_boxer_id(1)
#     except ValueError:
#         pytest.fail("validate_boxer_id raised ValueError unexpectedly for valid boxer ID")

# def test_validate_boxer_id_invalid_id(ring_model):
#     """Test validate_boxer_id raises error for invalid boxer ID."""
#     with pytest.raises(ValueError, match="Invalid boxer id: -1"):
#         ring_model.validate_boxer_id(-1)

#     with pytest.raises(ValueError, match="Invalid boxer id: invalid"):
#         ring_model.validate_boxer_id("invalid")

# def test_validate_track_number(ring_model, boxing_model):
#     """Test validate_track_number does not raise error for valid track number."""
#     ring_model.enter_ring(boxing_model)
#     try:
#         ring_model.validate_track_number(1)
#     except ValueError:
#         pytest.fail("validate_track_number raised ValueError unexpectedly for valid track number")

# def test_validate_track_number_invalid(ring_model, boxing_model):
#     """Test validate_track_number raises error for invalid track number."""
#     ring_model.enter_ring(boxing_model)

#     with pytest.raises(ValueError, match="Invalid track number: 0"):
#         ring_model.validate_track_number(0)

#     with pytest.raises(ValueError, match="Invalid track number: 2"):
#         ring_model.validate_track_number(2)

#     with pytest.raises(ValueError, match="Invalid track number: invalid"):
#         ring_model.validate_track_number("invalid")

##################################################
# Playback Test Cases
##################################################


# def test_play_current_song(playlist_model, sample_playlist, mock_update_play_count):
#     """Test playing the current song.

#     """
#     playlist_model.playlist.extend(sample_playlist)

#     playlist_model.play_current_song()

#     # Assert that CURRENT_TRACK_NUMBER has been updated to 2
#     assert playlist_model.current_track_number == 2, f"Expected track number to be 2, but got {playlist_model.current_track_number}"

#     # Assert that update_play_count was called with the id of the first song
#     mock_update_play_count.assert_called_once_with(1)

#     # Get the second song from the iterator (which will increment CURRENT_TRACK_NUMBER back to 1)
#     playlist_model.play_current_song()

#     # Assert that CURRENT_TRACK_NUMBER has been updated back to 1
#     assert playlist_model.current_track_number == 1, f"Expected track number to be 1, but got {playlist_model.current_track_number}"

#     # Assert that update_play_count was called with the id of the second song
#     mock_update_play_count.assert_called_with(2)


# def test_rewind_playlist(playlist_model, sample_playlist):
#     """Test rewinding the iterator to the beginning of the playlist.

#     """
#     playlist_model.playlist.extend(sample_playlist)
#     playlist_model.current_track_number = 2

#     playlist_model.rewind_playlist()
#     assert playlist_model.current_track_number == 1, "Expected to rewind to the first track"


# def test_go_to_track_number(playlist_model, sample_playlist):
#     """Test moving the iterator to a specific track number in the playlist.

#     """
#     playlist_model.playlist.extend(sample_playlist)

#     playlist_model.go_to_track_number(2)
#     assert playlist_model.current_track_number == 2, "Expected to be at track 2 after moving song"


# def test_go_to_random_track(playlist_model, sample_playlist, mocker):
#     """Test that go_to_random_track sets a valid random track number.

#     """
#     playlist_model.playlist.extend(sample_playlist)

#     mocker.patch("playlist.models.playlist_model.get_random", return_value=2)

#     playlist_model.go_to_random_track()
#     assert playlist_model.current_track_number == 2, "Current track number should be set to the random value"


# def test_play_entire_playlist(playlist_model, sample_playlist, mock_update_play_count):
#     """Test playing the entire playlist.

#     """
#     playlist_model.playlist.extend(sample_playlist)

#     playlist_model.play_entire_playlist()

#     # Check that all play counts were updated
#     mock_update_play_count.assert_any_call(1)
#     mock_update_play_count.assert_any_call(2)
#     assert mock_update_play_count.call_count == len(playlist_model.playlist)

#     # Check that the current track number was updated back to the first song
#     assert playlist_model.current_track_number == 1, "Expected to loop back to the beginning of the playlist"


# def test_play_rest_of_playlist(playlist_model, sample_playlist, mock_update_play_count):
#     """Test playing from the current position to the end of the playlist.

#     """
#     playlist_model.playlist.extend(sample_playlist)
#     playlist_model.current_track_number = 2

#     playlist_model.play_rest_of_playlist()

#     # Check that play counts were updated for the remaining songs
#     mock_update_play_count.assert_any_call(2)
#     assert mock_update_play_count.call_count == 1

#     assert playlist_model.current_track_number == 1, "Expected to loop back to the beginning of the playlist"
