from archiver import helpers
import logging
import configparser
from enum import Enum
from typing import List
import re
from abc import ABC, abstractmethod

class SuccessCondition(ABC):
    @abstractmethod
    def check(self, sp) -> bool:
        pass

    @staticmethod
    def parse_check(condition_str: str):
        condition_str_clean = condition_str.strip()

        contains_pattern = re.compile(r'CONTAINS\("([^)]*)"\)')
        contains_match = contains_pattern.match(condition_str_clean)

        if condition_str_clean == 'RETURN_ZERO':
            return ReturnZeroCondition()
        elif condition_str_clean == 'EMPTY_OUTPUT':
            return EmptyOutputCondition()
        elif contains_match:
            return ContainsCondition(contains_match.group(1))
        else:
            raise ValueError(f"Don't know/cannot parse success condition: {condition_str_clean}")


class ReturnZeroCondition(SuccessCondition):
    def check(self, sp):
        return sp.returncode == 0


class EmptyOutputCondition(SuccessCondition):
    def check(self, sp):
        return len(sp.stdout) == 0


class ContainsCondition(SuccessCondition):
    def __init__(self, txt: str):
        self.txt = txt

    def check(self, sp):
        return self.txt in sp.stdout.decode('UTF-8') # TODO: how to include enocding!?


class CmdBasedCheck:
    def __init__(self, name, precondition, precondition_failure_msg, check_cmd, success_conditions: List[SuccessCondition], check_failure_msg):
        self.name = name
        self.precondition = precondition
        self.precondition_failure_msg = precondition_failure_msg

        self.check_cmd = check_cmd
        self.success_conditions = success_conditions
        self.check_failure_msg: str = check_failure_msg

    def run_precondition(self):
        sp = helpers.run_shell_cmd(self.precondition)

        if sp.returncode != 0:
            logging.error(f"Command {self.precondition} failed with {sp.stdout}. {self.precondition_failure_msg}")
            return False
        return True


    def run(self):
        logging.info('---------------------------------------------------------')
        logging.info(f'Running check {self.name}')

        if self.precondition and not self.run_precondition():
            logging.error("Precondition failed")

        sp = helpers.run_shell_cmd(self.check_cmd)

        is_success = all(c.check(sp) for c in self.success_conditions)

        if is_success:
            logging.info(f"Check {self.name} succeeded")
            return True
        else:
            logging.error(f"Check {self.name} failed. {self.check_failure_msg} Output was\n {sp.stdout.decode('UTF-8')}")
            return False


    @staticmethod
    def checks_from_configfile(path):
        config = configparser.ConfigParser()

        config.read(path)

        logging.debug(f"Found {len(config.sections())} checks")
        return [CmdBasedCheck(name, sec['precondition'], sec['precondition_failure_msg'],
                              sec['check_cmd'],
                              [SuccessCondition.parse_check(c) for c in sec['success_conditions'].split(',')],
                              sec['check_failure_msg'])
                for name, sec in config.items() if name != config.default_section]