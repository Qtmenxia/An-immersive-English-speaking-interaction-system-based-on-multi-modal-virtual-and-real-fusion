from autogen.agentchat import GroupChat, AssistantAgent, UserProxyAgent, GroupChatManager
from typing import Callable, Dict, Literal, Optional, Union,List


class RecorderAgent(AssistantAgent):
    def __init__(self,
                 name: str,
                 system_message: Optional[str] = "DEFAULT_SYSTEM_MESSAGE",
                 llm_config: Optional[Union[Dict, Literal[False]]] = None,
                 is_termination_msg: Optional[Callable[[Dict], bool]] = None,
                 max_consecutive_auto_reply: Optional[int] = None,
                 human_input_mode: Literal["ALWAYS", "NEVER", "TERMINATE"] = "NEVER",
                 action_set:List[str] = None,
                 description: Optional[str] = None, *args, **kwargs):
        super().__init__(name=name,
                         system_message=system_message + f"The action should selected in {action_set}",
                         llm_config = llm_config,
                         is_termination_msg=is_termination_msg,
                         max_consecutive_auto_reply=max_consecutive_auto_reply,
                         human_input_mode=human_input_mode,
                         description=description,
                         **kwargs)
