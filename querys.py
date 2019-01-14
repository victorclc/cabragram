LAST_RUN_ID = "SELECT run_id FROM c_run ORDER BY run_id DESC LIMIT 1"
ACTIVE_CYCLES_BUY_ORDERS = "SELECT symbol, price FROM c_order WHERE cycle_id IN (SELECT cycle_id FROM C_CYCLE WHERE status = 'ACTIVE' AND run_id = ({})) AND exec_amount > 0 AND type = 'BUY'".format(
    LAST_RUN_ID)
RUN_OVERVIEW = 'SELECT * FROM v_run_overview WHERE run_id = ({})'.format(LAST_RUN_ID)
RUN_DETAILS = 'SELECT * FROM v_run_details WHERE run_id = ({})'.format(LAST_RUN_ID)
