import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set


class PostMap:
    """Interface for postmap.

    Retrieves aliases and recipients from a mapping file."""

    def __init__(self, p: Path, emaildomain: str = None):
        """Parse postfix alias table and provide its data."""
        subprocess.check_call(
            ["/usr/sbin/postmap", str(p)],
            shell=False,
        )
        table = subprocess.check_output(
            ["/usr/sbin/postmap", "-s", str(p)], shell=False
        ).decode()
        aliases: Dict[str, List[str]] = {}
        recepients: Dict[str, Set[str]] = defaultdict(set)
        for line in table.split("\n"):
            if not line or line.startswith("#"):
                continue
            alias, recp = line.split("\t", maxsplit=1)
            alias = self.normalize_email(alias)
            if emaildomain is not None:
                if alias.split("@")[1].lower() != emaildomain:
                    continue
            recps = [self.normalize_email(r.rstrip(",")) for r in recp.split("\t")]
            aliases[alias] = recps
            for recp in recps:
                recepients[recp].add(alias)

        self._recepients = recepients
        self._aliases = aliases

    @staticmethod
    def normalize_email(email: str):
        return email.lower()

    def get_recepients_for_alias(self, alias: str):
        """Return list of all emails which are part of an alias."""
        return self._aliases[self.normalize_email(alias)]

    def get_aliases_for_recepient(self, email: str):
        """Return list of aliases which the given email is part of."""
        return self._recepients[self.normalize_email(email)]

    def get_aliases(self):
        """Return a list of all aliases."""
        return self._aliases.keys()

    def is_user_part_of_alias(self, alias: str, email: str):
        return self.normalize_email(email) in self._aliases[self.normalize_email(alias)]
