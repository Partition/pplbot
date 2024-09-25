from discord import ui, ButtonStyle, Interaction
from discord.ui import Button

class ConfirmView(ui.View):
    def __init__(self, timeout: float | None = None):
        super().__init__(timeout=timeout)
        self.value = None

    @ui.button(label='Confirm', style=ButtonStyle.green)
    async def confirm(self, interaction: Interaction, button: Button):
        self.value = True
        self.stop()

    @ui.button(label='Cancel', style=ButtonStyle.red)
    async def cancel(self, interaction: Interaction, button: Button):
        self.value = False
        self.stop()

