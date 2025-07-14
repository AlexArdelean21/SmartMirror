# import json
# import os
# from datetime import datetime
# from util.logger import logger
# from difflib import SequenceMatcher

# class CommandTrainer:
#     def __init__(self, training_file="user_profiles/command_training.json"):
#         self.training_file = training_file
#         self.training_data = self.load_training_data()
        
#     def load_training_data(self):
#         """Load existing training data"""
#         try:
#             if os.path.exists(self.training_file):
#                 with open(self.training_file, 'r') as f:
#                     return json.load(f)
#             else:
#                 return {
#                     'user_commands': {},
#                     'corrections': {},
#                     'successful_patterns': {},
#                     'failed_patterns': {}
#                 }
#         except Exception as e:
#             logger.error(f"Failed to load training data: {e}")
#             return {
#                 'user_commands': {},
#                 'corrections': {},
#                 'successful_patterns': {},
#                 'failed_patterns': {}
#             }
    
#     def save_training_data(self):
#         """Save training data to file"""
#         try:
#             os.makedirs(os.path.dirname(self.training_file), exist_ok=True)
#             with open(self.training_file, 'w') as f:
#                 json.dump(self.training_data, f, indent=2)
#         except Exception as e:
#             logger.error(f"Failed to save training data: {e}")
    
#     def record_command_attempt(self, user_id, original_command, recognized_command, success):
#         """Record a command attempt for training"""
#         if user_id not in self.training_data['user_commands']:
#             self.training_data['user_commands'][user_id] = []
        
#         attempt = {
#             'timestamp': datetime.now().isoformat(),
#             'original': original_command,
#             'recognized': recognized_command,
#             'success': success
#         }
        
#         self.training_data['user_commands'][user_id].append(attempt)
        
#         # Keep only last 100 attempts per user
#         if len(self.training_data['user_commands'][user_id]) > 100:
#             self.training_data['user_commands'][user_id] = self.training_data['user_commands'][user_id][-100:]
        
#         self.save_training_data()
    
#     def add_correction(self, user_id, failed_command, corrected_command):
#         """Add a correction for failed commands"""
#         if user_id not in self.training_data['corrections']:
#             self.training_data['corrections'][user_id] = {}
        
#         failed_lower = failed_command.lower()
#         if failed_lower not in self.training_data['corrections'][user_id]:
#             self.training_data['corrections'][user_id][failed_lower] = []
        
#         self.training_data['corrections'][user_id][failed_lower].append({
#             'timestamp': datetime.now().isoformat(),
#             'correction': corrected_command
#         })
        
#         self.save_training_data()
    
#     def get_user_corrections(self, user_id, command):
#         """Get corrections for a specific command"""
#         if user_id in self.training_data['corrections']:
#             command_lower = command.lower()
#             if command_lower in self.training_data['corrections'][user_id]:
#                 corrections = self.training_data['corrections'][user_id][command_lower]
#                 # Return most recent correction
#                 return corrections[-1]['correction'] if corrections else None
#         return None
    
#     def get_user_patterns(self, user_id):
#         """Get successful command patterns for a user"""
#         if user_id not in self.training_data['user_commands']:
#             return {}
        
#         successful_commands = [
#             cmd['original'] for cmd in self.training_data['user_commands'][user_id]
#             if cmd['success']
#         ]
        
#         patterns = {}
#         for cmd in successful_commands:
#             words = cmd.lower().split()
#             for i in range(len(words) - 1):
#                 pattern = f"{words[i]} {words[i+1]}"
#                 if pattern not in patterns:
#                     patterns[pattern] = 0
#                 patterns[pattern] += 1
        
#         # Return patterns that appear more than once
#         return {k: v for k, v in patterns.items() if v > 1}
    
#     def suggest_correction(self, user_id, failed_command):
#         """Suggest a correction based on training data"""
#         # First check for exact corrections
#         exact_correction = self.get_user_corrections(user_id, failed_command)
#         if exact_correction:
#             return exact_correction
        
#         # Check for similar successful commands
#         if user_id in self.training_data['user_commands']:
#             successful_commands = [
#                 cmd['original'] for cmd in self.training_data['user_commands'][user_id]
#                 if cmd['success']
#             ]
            
#             best_match = None
#             best_score = 0
            
#             for successful_cmd in successful_commands:
#                 score = SequenceMatcher(None, failed_command.lower(), successful_cmd.lower()).ratio()
#                 if score > best_score and score > 0.6:
#                     best_score = score
#                     best_match = successful_cmd
            
#             return best_match
        
#         return None

# # Global trainer instance
# command_trainer = CommandTrainer()

# def train_command_recognition(user_id, original_command, recognized_command, success):
#     """Train the system with command recognition results"""
#     command_trainer.record_command_attempt(user_id, original_command, recognized_command, success)

# def add_command_correction(user_id, failed_command, corrected_command):
#     """Add a correction for a failed command"""
#     command_trainer.add_correction(user_id, failed_command, corrected_command)

# def get_command_suggestion(user_id, failed_command):
#     """Get a suggestion for a failed command"""
#     return command_trainer.suggest_correction(user_id, failed_command)

# def get_user_command_patterns(user_id):
#     """Get command patterns for a specific user"""
#     return command_trainer.get_user_patterns(user_id) 