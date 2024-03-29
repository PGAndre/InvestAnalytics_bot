from aiogram.utils.callback_data import CallbackData

user_callback = CallbackData("user", "action")
analytic_callback = CallbackData("analytic", "action")
predict_callback = CallbackData("predict", "ticker", "action")
user_predict_callback = CallbackData("user_predict", "ticker", "action")
admin_callback = CallbackData("admin", "action")
list_analytic_callback = CallbackData("admin", "id", "is_active", "action")
user_list_analytic_callback = CallbackData("admin", "id", "is_active", "action")
list_my_predicts_callback = CallbackData("predict", "ticker", "action")