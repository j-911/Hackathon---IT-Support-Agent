import datetime

class Ticket:
    """A simple class to represent an IT support ticket."""
    def __init__(self, ticket_id, description):
        self.id = ticket_id
        self.description = description
        self.status = "New"
        self.created_at = datetime.datetime.now()
        self.log = [f"{self.created_at.isoformat()}: Ticket created. Status: New. Description: {description}"]

    def update_status(self, new_status, reason=""):
        """Updates the ticket's status and returns a log string."""
        self.status = new_status
        log_entry = f"{datetime.datetime.now().isoformat()}: Status changed to {new_status}. Reason: {reason}"
        self.log.append(log_entry)
        return f"Ticket {self.id} status updated to '{self.status}'."

    def __str__(self):
        return (
            f"--- Ticket ID: {self.id} ---\n"
            f"   Status: {self.status}\n"
            f"   Description: {self.description}\n"
            f"   Created: {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"   --- Log ---\n" + "\n".join([f"     - {entry}" for entry in self.log]) +
            "\n   --------------"
        )