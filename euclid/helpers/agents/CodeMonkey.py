from const.function_calls import GET_FILES, DEV_STEPS, IMPLEMENT_CHANGES, CODE_CHANGES
from helpers.files import update_file
from helpers.cli import run_command_until_success
from helpers.cli import build_directory_tree
from helpers.AgentConvo import AgentConvo
from helpers.Agent import Agent

class CodeMonkey(Agent):
    def __init__(self, project, developer):
        super().__init__('code_monkey', project)
        self.developer = developer

    def implement_code_changes(self, code_changes_description):
        convo = AgentConvo(self)
        steps = convo.send_message('development/task/break_down_code_changes.prompt', {
            "instructions": code_changes_description,
            "directory_tree": self.project.get_directory_tree(),
            "technologies": self.project.architecture
        }, CODE_CHANGES)


        convo.save_branch('after_code_changes_breakdown')
        for i, step in enumerate(steps):
            convo.load_branch('after_code_changes_breakdown')
            if step['type'] == 'command':
                run_command_until_success(step['command'], step['command_timeout'], convo)
            elif step['type'] == 'code_change':
                files_needed = convo.send_message('development/task/request_files_for_code_changes.prompt', {
                    "instructions": code_changes_description,
                    "step_description": step['code_change_description'],
                    "directory_tree": self.project.get_directory_tree(),
                }, GET_FILES)

                changes = convo.send_message('development/implement_changes.prompt', {
                    "instructions": code_changes_description,
                    "directory_tree": self.project.get_directory_tree(),
                    "files": self.project.get_files(files_needed),
                }, IMPLEMENT_CHANGES)

                for file_data in changes:
                    update_file(self.project.get_full_file_path(file_data['name']), file_data['content'])
        
                self.developer.test_code_changes(self, convo)

    def implement_test(self, convo, automated_test_description):
        files_needed = convo.send_message('development/task/request_test_files.prompt', {
            "testing_files_tree": self.project.get_directory_tree(),
        }, GET_FILES)

        changes = convo.send_message('development/write_automated_test.prompt', {
            "files": self.project.get_files(files_needed),
        }, IMPLEMENT_CHANGES)

        for file_data in changes:
            update_file(self.project.get_full_file_path(file_data['name']), file_data['content'])

        self.developer.run_test_and_debug()
        self.developer.run_all_tests_and_debug()
