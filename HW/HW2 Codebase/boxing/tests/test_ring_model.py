from contextlib import contextmanager

import pytest
from boxing.models.boxers_model import Boxer
from boxing.models.ring_model import RingModel
from boxing.utils.sql_utils import get_db_connection


@pytest.fixture()
def sample_boxer1():
    return Boxer(id=1, name='Boxer 1', weight=180, height=70, reach=75, age=30, weight_class='MIDDLEWEIGHT')

@pytest.fixture()
def sample_boxer2():
    return Boxer(id=2, name='Boxer 2', weight=175, height=68, reach=72, age=28, weight_class='MIDDLEWEIGHT')

@pytest.fixture()
def sample_boxer3():
    return Boxer(id=3, name='Boxer 3', weight=176, height=69, reach=73, age=29, weight_class='MIDDLEWEIGHT')

@pytest.fixture()
def ring_model():
    """Fixture to provide a new instance of RingModel for each test."""
    return RingModel()


def test_enter_ring_valid_boxer(ring_model, sample_boxer1):
    """Test that a valid Boxer can be added to the ring.

    """
    
    ring_model.enter_ring(sample_boxer1)
    assert len(ring_model.ring) == 1, "Ring should contain one boxer."
    assert ring_model.ring[0] == sample_boxer1, "The added boxer is not in the ring."



def test_enter_ring_two_boxers(ring_model, sample_boxer1,sample_boxer2):
    """Test that 2 valid Boxers can be added to the ring.

    """
    ring_model.enter_ring(sample_boxer1)
    ring_model.enter_ring(sample_boxer2)
    assert len(ring_model.ring) == 2, "Ring should contain two boxers."
    assert ring_model.ring[0] == sample_boxer1, "The first boxer is not in the ring."
    assert ring_model.ring[1] == sample_boxer2, "The second boxer is not in the ring."

    

def test_enter_ring_while_full(ring_model, sample_boxer1, sample_boxer2, sample_boxer3):
    """Test error when trying add a Boxer to a full ring.

    """
    ring_model.enter_ring(sample_boxer1)
    ring_model.enter_ring(sample_boxer2)
    
    with pytest.raises(ValueError, match="Ring is full, cannot add more boxers."):
        ring_model.enter_ring(sample_boxer3)

def test_enter_ring_invalid_type(ring_model):
    """Test error when adding a non-Boxer object.

    """
    nonboxer = "NOT A BOXER"
    
    with pytest.raises(TypeError, match="Invalid type: Expected 'Boxer'"):
        ring_model.enter_ring(nonboxer)

def test_fight_with_insufficient_boxers(ring_model, sample_boxer1):
    """
    Test that starting a fight with fewer than two boxers.
    """
    ring_model.enter_ring(sample_boxer1)

    with pytest.raises(ValueError, match="There must be two boxers to start a fight."):
        ring_model.fight()

def test_clear_ring(ring_model, sample_boxer1, sample_boxer2):
    """
    Test to clear the ring.
    """

    ring_model.enter_ring(sample_boxer1)
    ring_model.enter_ring(sample_boxer2)

    assert len(ring_model.ring) == 2, "Ring should contain two boxers."

    ring_model.clear_ring()
    assert len(ring_model.ring) == 0, "Ring should be empty after clearing."

def test_get_boxers(ring_model, sample_boxer1, sample_boxer2):
    """
    Test to get the boxers in the ring.
    """
    
    ring_model.enter_ring(sample_boxer1)
    ring_model.enter_ring(sample_boxer2)

    boxers = ring_model.get_boxers()

    assert len(boxers) == 2, "Should retrieve the two boxers from the ring."
    assert boxers[0] == sample_boxer1, "First boxer does not match."
    assert boxers[1] == sample_boxer2, "Second boxer does not match."

def test_get_fighting_skill(ring_model, sample_boxer1):
    """
    Test the `get_fighting_skill` method calculates skill correctly.
    """
 
    skill = ring_model.get_fighting_skill(sample_boxer1)

    expected_skill = (180 * len(sample_boxer1.name)) + (75 / 10)  # Simplified calculation
    assert skill == expected_skill, f"Expected skill to be {expected_skill}, got {skill}."

def test_fight_valid(mock_clear_ring, mock_update_boxer_stats, mock_get_random, mock_get_fighting_skill, ring_model, sample_boxer1, sample_boxer2):
    """Test a valid fight with two boxers."""
    # Add two boxers to the ring
    ring_model.enter_ring(sample_boxer1)
    ring_model.enter_ring(sample_boxer2)

    # Define the fighting skills of each boxer
    mock_get_fighting_skill.side_effect = [10, 5]  # boxer_1 skill = 10, boxer_2 skill = 5

    # Simulate a random number for the fight outcome (Boxer 1 wins)
    mock_get_random.return_value = 0.8

    # Run the fight method
    winner = ring_model.fight()

    # Assertions
    mock_get_fighting_skill.assert_any_call(sample_boxer1)  # Ensure skill of boxer_1 was fetched
    mock_get_fighting_skill.assert_any_call(sample_boxer2)  # Ensure skill of boxer_2 was fetched
    mock_get_random.assert_called_once()  # Ensure random number was generated
    mock_update_boxer_stats.assert_any_call(sample_boxer1.id, 'win')  # Ensure winner stats updated
    mock_update_boxer_stats.assert_any_call(sample_boxer2.id, 'loss')  # Ensure loser stats updated
    mock_clear_ring.assert_called_once()  # Ensure the ring was cleared

    assert winner == sample_boxer1.name  # Ensure the winner is boxer_1

def test_fight_insufficient_boxers(ring_model, sample_boxer1):
    """
    Test the fight when there are less than two boxers in the ring.
    """
  
    ring_model.enter_ring(sample_boxer1)
    
    try:
        ring_model.fight()
        assert False, "ValueError expected but not raised."
    except ValueError as e:
        assert str(e) == "There must be two boxers to start a fight.", f"Unexpected error message: {str(e)}"
