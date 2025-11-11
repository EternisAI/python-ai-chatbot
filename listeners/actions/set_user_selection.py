from logging import Logger
from slack_bolt import Ack
from state_store.set_user_state import set_user_state


def set_user_selection(logger: Logger, ack: Ack, body: dict):
    try:
        ack()
        user_id = body["user"]["id"]
        value = body["actions"][0]["selected_option"]["value"]
        
        logger.info(f"[set_user_selection] User {user_id} selected: {value}")
        
        if value != "null":
            # parsing the selected option value from the options array in app_home_opened.py
            selected_provider, selected_model = (
                value.split(" ")[-1],
                value.split(" ")[0],
            )
            
            logger.info(f"[set_user_selection] Setting provider={selected_provider}, model={selected_model}")
            set_user_state(user_id, selected_provider, selected_model)
            logger.info(f"[set_user_selection] User state updated successfully!")
        else:
            logger.warning(f"[set_user_selection] Null selection received from user {user_id}")
            raise ValueError("Please make a selection")
    except Exception as e:
        logger.error(f"[set_user_selection] ERROR: {type(e).__name__}: {str(e)}", exc_info=True)
