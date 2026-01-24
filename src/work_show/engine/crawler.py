from ..core.protocols import DataSource, DataStorage, Deduplicator, DedupAction
from ..utils.logger import get_logger
import random
from ..data_clean import mapping_table
from ..deduplicator.set_deduplicator import SetDeduplicator

logger = get_logger("CrawlerEngine")


class CrawlerEngine:
    def __init__(
        self,
        source: DataSource,
        storage: DataStorage,
        config: dict,
        deduplicator: Deduplicator = SetDeduplicator(set()),
    ):
        self.source = source
        self.storage = storage
        self.deduplicator = deduplicator
        # 从配置中读取熔断阈值
        self.max_consecutive_duplicates = config.get("max_consecutive_duplicates", 10)
        self.dedup_filters = config.get("dedup_filters", {})
        self.total_saved = 0
        self._register_handlers()
        self.deduplicator.merge_set(
            source.fetch_all_fingerprints(storage, self.dedup_filters)
        )

    def _register_handlers(self):
        self._handlers = {}
        for name in dir(self):
            method = getattr(self, name)
            if hasattr(method, "_dedup_action"):
                self._handlers[method._dedup_action] = method

    @staticmethod
    def dedup_action(action: DedupAction):
        def decorator(func):
            func._dedup_action = action
            return func

        return decorator

    @dedup_action(DedupAction.SAVE)
    def _action_save(self, item, args=None):
        try:
            item = self.source.extract_by_llm(item)
            self.storage.save(item)
            self.total_saved += 1
            logger.info(f"{self.source.__class__.__name__}写入成功")
            if self.total_saved % 100 == 0:
                logger.info(
                    f"Progress: Saved {self.total_saved} items..., Source: {item.source_platform}"
                )
        except Exception as e:
            logger.error(
                f"Failed to save item {item.job_id}, source: {item.source_platform}: {e}"
            )

    @dedup_action(DedupAction.SKIP)
    def _action_skip(self, item, args=None):
        pass

    @dedup_action(DedupAction.STOP)
    def _action_stop(self, item, args=None):
        logger.warning(
            f"Stop signal received. Stopping crawling at item {item.job_id}."
        )
        return "STOP"

    @dedup_action(DedupAction.SKIP_PAGES)
    def _action_skip_pages(self, item, args=None):
        if args is not None and isinstance(args, int) and args > 0:
            logger.info(
                f"Consecutive duplicates detected. Skipping {args} pages. Source: {item.source_platform}"
            )
            self.source.skip_pages(args)

    @dedup_action(DedupAction.UPDATE)
    def _action_update(self, item, args=None):
        pass

    def run(self):
        self.total_saved = 0
        logger.info(f"Start crawling from source: {type(self.source).__name__}")
        try:
            for item in self.source.fetch_items():
                dedup_response = self.deduplicator.check_status(item)
                handler = self._handlers.get(dedup_response.action)

                if handler:
                    result = handler(item, dedup_response.args)
                    if result == "STOP":
                        break
                else:
                    logger.warning(f"Unknown dedup action: {dedup_response.action}")

        except Exception as e:
            logger.critical(f"Critical Engine Error: {e}")
        finally:
            logger.info(f"Crawling finished. Total new items: {self.total_saved}")
