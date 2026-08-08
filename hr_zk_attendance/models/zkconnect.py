from zk import ZK
import odoorpc
import time

DEVICE_IP = "192.168.1.210"
ODOO_URL = "tappy.applified.co.in"
ODOO_DB = "tappy_toes"
ODOO_USER = "tappy_toes"
ODOO_PASS = "tappy_toes"

# Connect to device
zk = ZK(DEVICE_IP, port=4370, timeout=5)
conn = zk.connect()
print("conn ", conn)

# Connect to Odoo (HTTPS connection)
odoo = odoorpc.ODOO(ODOO_URL, port=443, protocol='jsonrpc+ssl')
odoo.login(ODOO_DB, ODOO_USER, ODOO_PASS)

while True:
    attendance = conn.get_attendance()
    # print("attendence ", attendance.json())
    for att in attendance:
        print(att.user_id)
    #     odoo.env['zk.machine.attendance'].create({
    #         'device_id_num': att.user_id,
    #         'check_in': att.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
    #     })
    #     employee = odoo.env['hr.employee'].search([('device_id_num', '=', att.user_id)])
    #     # print("employee", employee[0])
    #     odoo.env['hr.attendance'].create({
    #         'employee_id': employee[0],
    #         'check_in': att.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
    #     })
    # time.sleep(60)
