import configparser
import logging
import os
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Union

from archiver import helpers

CHECK_SEP_STR = '---------------------------------------------------------------'

WDIR_REPLACMENT_TAG = '{WDIR}'


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
        return self.txt in sp.stdout.decode()


class CmdBasedCheck:
    def __init__(self, name: str, precondition: str,
                 precondition_failure_msg: str, check_cmd: str,
                 success_conditions: List[SuccessCondition], check_failure_msg: str):
        self.name = name
        self.precondition = precondition
        self.precondition_failure_msg = precondition_failure_msg

        self.check_cmd = check_cmd
        self.success_conditions = success_conditions
        self.check_failure_msg: str = check_failure_msg

    def run_precondition(self):
        if not self.precondition:
            return True

        sp = helpers.run_shell_cmd(self.precondition)

        if sp.returncode != 0:
            logging.error(f"Command {self.precondition} failed with {sp.stdout}:")
            logging.error(f"  {self.precondition_failure_msg}")
            return False
        return True

    def run(self, wdir: Union[str, Path]):
        os.chdir(wdir)

        logging.info(CHECK_SEP_STR)
        logging.info(f'Running check {self.name}')

        sp = helpers.run_shell_cmd(self.check_cmd, check_returncode=False)

        is_success = all(c.check(sp) for c in self.success_conditions)

        if is_success:
            logging.info(f"Check {self.name} succeeded")
            return True
        else:
            logging.error(f"Check {self.name} failed. "
                          f"{self.check_failure_msg.replace(WDIR_REPLACMENT_TAG, str(wdir))}\n"
                          f"Output was\n{sp.stdout.decode()}")
            return False


    @staticmethod
    def checks_from_configfile(path: Path):
        if not path.exists():
           raise FileNotFoundError(f"Could not find path {path}")

        config = configparser.ConfigParser()

        config.read(path)

        nr_checks = len(config.sections())

        if nr_checks == 0:
            raise ValueError(f"No checks found in {path}")

        logging.debug(f"Found {nr_checks} checks")
        return [CmdBasedCheck(name, sec['precondition'],
                              sec['precondition_failure_msg'],
                              sec['check_cmd'],
                              [SuccessCondition.parse_check(c) for c in sec['success_conditions'].split(',')],
                              sec['check_failure_msg'])
                for name, sec in config.items() if
                name != config.default_section]
