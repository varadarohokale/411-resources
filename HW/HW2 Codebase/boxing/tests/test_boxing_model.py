import pytest
import re
from boxing.models.boxers_model import Boxer, create_boxer, delete_boxer, get_boxer_by_id, get_boxer_by_name, update_boxer_stats
from boxing.models.ring_model import RingModel
from contextlib import contextmanager
import sqlite3

def normalize_whitespace(sql_query: str) -> str:
    return re.sub(r'\s+', ' ', sql_query).strip()

# Mocking the database connection for tests
@pytest.fixture
def mock_cursor(mocker):
    mock_conn = mocker.Mock()
    mock_cursor = mocker.Mock()

    # Mock the connection's cursor
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # Default return for queries
    mock_cursor.fetchall.return_value = []
    mock_cursor.commit.return_value = None

    # Mock the get_db_connection context manager from sql_utils
    @contextmanager
    def mock_get_db_connection():
        yield mock_conn  # Yield the mocked connection object

    mocker.patch("boxing.models.boxers_model.get_db_connection", mock_get_db_connection)

    return mock_cursor  # Return the mock cursor so we can set expectations per test


@pytest.fixture()
def sample_boxer1():
    return Boxer(id=1, name='Boxer 1', weight=180, height=70, reach=75, age=30, weight_class='MIDDLEWEIGHT')


@pytest.fixture()
def sample_boxer2():
    return Boxer(id=2, name='Boxer 2', weight=175, height=68, reach=72, age=28, weight_class='MIDDLEWEIGHT')


@pytest.fixture()
def ring_model():
    """Fixture to provide a new instance of RingModel for each test."""
    return RingModel()


##################################################
# Add and Remove Boxer Management Test Cases
##################################################

def test_create_boxer(mock_cursor):
    """Test creating a new boxer in the database."""
    create_boxer('Boxer 1', 180, 70, 75, 30)
    
    expected_query = normalize_whitespace("""INSERT INTO boxers (name, weight, height, reach, age) 
                                            VALUES (?, ?, ?, ?, ?)""")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])
    
    # Verify the SQL query structure
    assert actual_query == expected_query, f"Expected query: {expected_query}, but got: {actual_query}"
    
    # Verify the query arguments
    actual_arguments = mock_cursor.execute.call_args[0][1]
    expected_arguments = ('Boxer 1', 180, 70, 75, 30)
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."


def test_create_boxer_invalid_weight():
    """Test creating a boxer with an invalid weight."""
    with pytest.raises(ValueError, match="Invalid weight: 100. Must be at least 125."):
        create_boxer('Boxer 1', 100, 70, 75, 30)


def test_delete_boxer(mock_cursor):
    """Test deleting a boxer from the catalog by boxer ID."""
    
    # Simulate the existence of a boxer with id=1
    # We can use any value other than None to indicate the boxer exists
    mock_cursor.fetchone.return_value = (1, 'Boxer 1', 180, 70, 75, 30)

    delete_boxer(1)

    # Expected queries for selecting and deleting a boxer
    expected_select_sql = normalize_whitespace("""SELECT id FROM boxers WHERE id = ?""")
    expected_delete_sql = normalize_whitespace("""DELETE FROM boxers WHERE id = ?""")

    # Access both calls to `execute()` using `call_args_list`
    actual_select_sql = normalize_whitespace(mock_cursor.execute.call_args_list[0][0][0])
    actual_delete_sql = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    # Assert that the SQL query structure matches
    assert actual_select_sql == expected_select_sql, """The SELECT query did not match the expected structure."""
    assert actual_delete_sql == expected_delete_sql, """The DELETE query did not match the expected structure."""

    # Ensure the correct arguments were used in both SQL queries
    expected_select_args = (1,)
    expected_delete_args = (1,)

    actual_select_args = mock_cursor.execute.call_args_list[0][0][1]
    actual_delete_args = mock_cursor.execute.call_args_list[1][0][1]

    # Assert the arguments match as well
    assert actual_select_args == expected_select_args, f"The SELECT query arguments did not match. Expected {expected_select_args}, got {actual_select_args}."
    assert actual_delete_args == expected_delete_args, f"The DELETE query arguments did not match. Expected {expected_delete_args}, got {actual_delete_args}."


def test_delete_boxer_not_found(mock_cursor):
    """Test deleting a boxer that doesn't exist."""
    mock_cursor.execute.side_effect = ValueError("Boxer with ID 999 not found.")
    
    with pytest.raises(ValueError, match="Boxer with ID 999 not found."):
        delete_boxer(999)


##################################################
# Boxer Retrieval Test Cases
##################################################

def test_get_boxer_by_id(mock_cursor, sample_boxer1):
    """Test retrieving a boxer by ID."""
    mock_cursor.fetchone.return_value = (sample_boxer1.id, sample_boxer1.name, sample_boxer1.weight,
                                         sample_boxer1.height, sample_boxer1.reach, sample_boxer1.age)
    
    result = get_boxer_by_id(1)
    
    assert result.id == sample_boxer1.id
    assert result.name == sample_boxer1.name


def test_get_boxer_by_id_not_found(mock_cursor):
    """Test retrieving a boxer by ID when the boxer does not exist."""
    mock_cursor.fetchone.return_value = None
    
    with pytest.raises(ValueError, match="Boxer with ID 999 not found."):
        get_boxer_by_id(999)


def test_get_boxer_by_name(mock_cursor, sample_boxer1):
    """Test retrieving a boxer by name."""
    mock_cursor.fetchone.return_value = (sample_boxer1.id, sample_boxer1.name, sample_boxer1.weight,
                                         sample_boxer1.height, sample_boxer1.reach, sample_boxer1.age)
    
    result = get_boxer_by_name('Boxer 1')
    
    assert result.id == sample_boxer1.id
    assert result.name == sample_boxer1.name


def test_get_boxer_by_name_not_found(mock_cursor):
    """Test retrieving a boxer by name when the boxer does not exist."""
    mock_cursor.fetchone.return_value = None
    
    with pytest.raises(ValueError, match="Boxer 'Boxer 999' not found."):
        get_boxer_by_name('Boxer 999')


##################################################
# Update Boxer Stats Test Cases
##################################################

def test_update_boxer_stats(mock_cursor, sample_boxer1, sample_boxer2):
    """Test updating stats for a boxer."""
    mock_cursor.fetchone.return_value = True
    
    # Simulate adding the boxers to the ring
    ring_model = RingModel()
    ring_model.enter_ring(sample_boxer1)
    ring_model.enter_ring(sample_boxer2)
    
    # Simulate a fight and update stats
    result = ring_model.fight()
    
    assert result in [sample_boxer1.name, sample_boxer2.name]
    mock_cursor.execute.assert_any_call("""UPDATE boxers SET fights = fights + 1, wins = wins + 1 WHERE id = ?""", (sample_boxer1.id,))
    mock_cursor.execute.assert_any_call("""UPDATE boxers SET fights = fights + 1 WHERE id = ?""", (sample_boxer2.id,))
