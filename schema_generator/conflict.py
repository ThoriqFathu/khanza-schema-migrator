from collections.abc import Callable
from dataclasses import dataclass

from .models import Conflict


@dataclass(frozen=True)
class ConflictDecision:
    decision: str
    remember_for_table: bool = False


ConflictCallback = Callable[
    [str, str, str, str, str],
    ConflictDecision | str,
]


class ConflictResolver:
    def __init__(
        self,
        callback: ConflictCallback | None = None,
    ):
        self.table_decisions: dict[str, str] = {}
        self.callback = callback

    def resolve(
        self,
        object_type: str,
        table: str,
        name: str,
        existing: str,
        khanza: str,
    ) -> Conflict:

        # ========================================================
        # REMEMBERED DECISION
        # ========================================================

        if table in self.table_decisions:
            decision = self.table_decisions[table]

            return Conflict(
                object_type=object_type,
                table=table,
                name=name,
                existing=existing,
                khanza=khanza,
                decision=decision,
            )

        # ========================================================
        # CALLBACK
        # ========================================================

        if self.callback is not None:

            callback_result = self.callback(
                object_type,
                table,
                name,
                existing,
                khanza,
            )

            # ----------------------------------------------------
            # Callback boleh mengembalikan string lama:
            #
            # "E"
            # "K"
            # "S"
            #
            # Ini menjaga kompatibilitas dengan test_callback.py
            # yang sekarang.
            # ----------------------------------------------------

            if isinstance(callback_result, str):
                decision = callback_result.upper()
                remember_for_table = False

            # ----------------------------------------------------
            # Callback GUI bisa mengembalikan:
            #
            # ConflictDecision(
            #     decision="K",
            #     remember_for_table=True,
            # )
            # ----------------------------------------------------

            elif isinstance(
                callback_result,
                ConflictDecision,
            ):
                decision = callback_result.decision.upper()
                remember_for_table = (
                    callback_result.remember_for_table
                )

            else:
                raise TypeError(
                    "Conflict callback harus mengembalikan "
                    "str atau ConflictDecision."
                )

            # ----------------------------------------------------
            # VALIDASI DECISION
            # ----------------------------------------------------

            if decision not in {"E", "K", "S"}:
                raise ValueError(
                    f"Invalid conflict decision: {decision}. "
                    "Gunakan E, K, atau S."
                )

            # ----------------------------------------------------
            # SIMPAN KEPUTUSAN UNTUK TABEL
            # ----------------------------------------------------

            if remember_for_table:
                self.table_decisions[table] = decision

        # ========================================================
        # TERMINAL
        # ========================================================

        else:
            decision = self._resolve_terminal(
                object_type,
                table,
                name,
                existing,
                khanza,
            )

        # ========================================================
        # RETURN CONFLICT
        # ========================================================

        return Conflict(
            object_type=object_type,
            table=table,
            name=name,
            existing=existing,
            khanza=khanza,
            decision=decision,
        )

    def _resolve_terminal(
        self,
        object_type: str,
        table: str,
        name: str,
        existing: str,
        khanza: str,
    ) -> str:

        print()
        print("=" * 80)
        print(f"{object_type.upper()} CONFLICT")
        print("=" * 80)
        print(f"Table : {table}")
        print(f"Name  : {name}")
        print()

        print("Existing:")
        print(f"  {existing}")

        print()
        print("Khanza:")
        print(f"  {khanza}")

        print()
        print("[E] Keep Existing")
        print("[K] Use Khanza")
        print("[S] Skip")
        print("[T] Use this choice for this table")

        while True:
            choice = input(
                "Choice [E/K/S/T]: "
            ).strip().upper()

            if choice in {"E", "K", "S", "T"}:
                break

            print(
                "Pilihan tidak valid. "
                "Gunakan E, K, S, atau T."
            )

        # ========================================================
        # REMEMBER FOR TABLE
        # ========================================================

        if choice == "T":

            while True:
                decision = input(
                    "Choice untuk semua conflict "
                    "tabel ini [E/K/S]: "
                ).strip().upper()

                if decision in {"E", "K", "S"}:
                    break

                print(
                    "Pilihan tidak valid. "
                    "Gunakan E, K, atau S."
                )

            self.table_decisions[table] = decision

            return decision

        return choice