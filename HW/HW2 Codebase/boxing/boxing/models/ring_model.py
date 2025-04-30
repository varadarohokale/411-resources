import logging
import math
from typing import List

from boxing.models.boxers_model import Boxer, update_boxer_stats
from boxing.utils.logger import configure_logger
from boxing.utils.api_utils import get_random


logger = logging.getLogger(__name__)
configure_logger(logger)


class RingModel:
    """
    Represents a boxing ring where boxers can be added, fight, and have their stats updated.

    Attributes:
        ring (List[Boxer]): A list containing the boxers currently in the ring.

    Methods:
        
    """
    def __init__(self):
        self.ring: List[Boxer] = []
        logger.info("RingModel initialized with an empty ring.")

    def fight(self) -> str:
        """
        Simulates a fight between two boxers.

        The outcome is determined based on their fighting skills (calculated
        using a logistic function to normalize the skill difference). 

        Returns:
            str: The name of the winner.

        Raises:
            ValueError: If there are less than two boxers in the ring.
        """

        logger.info("Starting a fight.")

        if len(self.ring) < 2:
            logger.warning("Not enough boxers in the ring to start a fight.")
            raise ValueError("There must be two boxers to start a fight.")

        boxer_1, boxer_2 = self.get_boxers()

        skill_1 = self.get_fighting_skill(boxer_1)
        skill_2 = self.get_fighting_skill(boxer_2)

        # Compute the absolute skill difference
        # And normalize using a logistic function for better probability scaling
        delta = abs(skill_1 - skill_2)
        normalized_delta = 1 / (1 + math.e ** (-delta))

        random_number = get_random()

        if random_number < normalized_delta:
            winner = boxer_1
            loser = boxer_2
        else:
            winner = boxer_2
            loser = boxer_1

        update_boxer_stats(winner.id, 'win')
        update_boxer_stats(loser.id, 'loss')

        self.clear_ring()
        logger.info("Fight occurred and ring cleared.")
        return winner.name

    def clear_ring(self):
        """
        Removes all boxers from the ring.
        """
        if not self.ring:
            logger.info("Ring is already empty.")
            return
        logger.info("Clearing ring.")
        self.ring.clear()

    def enter_ring(self, boxer: Boxer):
        """
        Adds a boxer to the ring.

        Args:
            boxer (Boxer): The boxer to enter the ring.

        Raises:
            TypeError: If the argument is not of type `Boxer`.
            ValueError: If the ring has two boxers in it.
        """
        if not isinstance(boxer, Boxer):
            logger.error(f"Invalid type: Expected 'Boxer', got '{type(boxer).__name__}'.")
            raise TypeError(f"Invalid type: Expected 'Boxer', got '{type(boxer).__name__}'")

        if len(self.ring) >= 2:
            logger.error("Ring is full, cannot add more boxers.")
            raise ValueError("Ring is full, cannot add more boxers.")

        self.ring.append(boxer)
        logger.info(f"Boxer {boxer.name} entered the ring sucessfully.")

    def get_boxers(self) -> List[Boxer]:
        """
        Retrieves the list of boxers currently in the ring.

        Returns:
            List[Boxer]: A list of boxers in the ring.
        """
        if not self.ring:
            pass
        else:
            pass
        
        logger.info("Retrieving boxers from the ring.")

        return self.ring

    def get_fighting_skill(self, boxer: Boxer) -> float:
        """
        Calculates the fighting skill of a boxer based on their specific attributes.

        The skill is computed in an arbitrary calculation that involves the boxer's weight,
        name length, reach, and age.

        Args:
            boxer (Boxer): The boxer whose skill is being calculated.

        Returns:
            float: The fighting skill of the boxer.
        """
        logger.info(f"Calculating fighting skill for boxer {boxer.name}.")

        # Arbitrary calculations
        age_modifier = -1 if boxer.age < 25 else (-2 if boxer.age > 35 else 0)
        skill = (boxer.weight * len(boxer.name)) + (boxer.reach / 10) + age_modifier

        logger.info(f"Fighting skill for {boxer.name}: {skill}.")
        return skill
