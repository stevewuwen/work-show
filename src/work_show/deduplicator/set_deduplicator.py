from dataclasses import dataclass
from ..utils.logger import get_logger
from ..core.models import Item
from ..core.protocols import DedupAction, DedupResponse
import random
import yaml

logger = get_logger("SetDeduplicator")


@dataclass
class SetDeduplicator:
    st: set
    consecutive_dup: int = 0
    config_path: str = "./config/settings.yaml"

    def __post_init__(self):
        config = yaml.safe_load(open(self.config_path))
        self.max_consecutive_duplicates = config["crawler"].get(
            "max_consecutive_duplicates", 7
        )

    def check_status(self, item: Item) -> DedupResponse:
        if item.job_id == None or item.job_id == "":
            return DedupResponse(DedupAction.SKIP)  # 表示当前这个不需要，因为id无效
        if item.job_id in self.st:
            self.consecutive_dup += 1
            logger.debug(
                f"发现重复: item job id: {item.job_id}, item source: {item.source_platform}"
            )
            if self.consecutive_dup >= self.max_consecutive_duplicates:
                logger.warning(
                    f"Feature Stop: Reached {self.consecutive_dup} consecutive duplicates. {item.source_platform} break"
                )
                return DedupResponse(DedupAction.STOP)  # 表示退出循环，停止爬取
            if self.consecutive_dup >= 3 and self.consecutive_dup % 3 == 0:
                skip_count = random.randint(0, 10 + self.consecutive_dup * 3)
                return DedupResponse(DedupAction.SKIP_PAGES, args=skip_count)
            return DedupResponse(DedupAction.SKIP)
        else:
            self.st.add(item.job_id)
            self.consecutive_dup = 0
            return DedupResponse(DedupAction.SAVE)  # 新数据，保存
        return DedupResponse(DedupAction.SAVE)  # 默认保存

    def merge_set(self, st: set) -> None:
        self.st = self.st.union(st)
