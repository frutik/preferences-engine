from django.core.management.base import BaseCommand
from django.utils import timezone

from preferences_engine.models import DECAY_THRESHOLD, UserPreferenceMemory, UserPreferenceMemoryEvent

BATCH_SIZE = 500


class Command(BaseCommand):
    help = "Mark decayed UserPreferenceMemory records as SUPERSEDED"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report counts without writing any changes",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        now = timezone.now()
        expired = 0
        checked = 0

        qs = (
            UserPreferenceMemory.objects
            .filter(status=UserPreferenceMemory.Status.ACTIVE)
            .only("id", "user_id", "importance", "confidence", "decay", "updated_at")
        )

        batch = []
        event_batch = []

        for memory in qs.iterator(chunk_size=BATCH_SIZE):
            checked += 1

            if memory.effective_score(now=now) >= DECAY_THRESHOLD:
                continue

            expired += 1

            if not dry_run:
                memory.status = UserPreferenceMemory.Status.SUPERSEDED
                batch.append(memory)
                event_batch.append(UserPreferenceMemoryEvent(
                    user_id=memory.user_id,
                    memory=memory,
                    action=UserPreferenceMemoryEvent.Action.IGNORE,
                    reasoning=f"Expired by decay: effective_score={memory.effective_score(now=now):.4f} < {DECAY_THRESHOLD}",
                ))

            if len(batch) >= BATCH_SIZE:
                self._flush(batch, event_batch)
                batch.clear()
                event_batch.clear()

        if batch:
            self._flush(batch, event_batch)

        label = "[dry-run] " if dry_run else ""
        self.stdout.write(
            f"{label}checked={checked} expired={expired}"
        )

    def _flush(self, memories, events):
        UserPreferenceMemory.objects.bulk_update(memories, ["status"])
        UserPreferenceMemoryEvent.objects.bulk_create(events)
