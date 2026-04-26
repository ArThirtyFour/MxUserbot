import asyncio
import html

from ...core import loader, utils


class Meta:
    name = "Shell"
    description = "Execute shell commands"
    version = "1.0.0"
    tags = ["system", "admin"]


@loader.tds
class ShellModule(loader.Module):

    strings = {
        "name": "Shell",
        "executing": "<b>⚙️ | Executing command...</b>",
        "result": "<b>📟 | Command:</b> <code>{}</code><br><b>📤 | Output:</b><br><code>{}</code>",
        "error": "<b>❌ | Error executing command:</b><br><pre>{}</pre>",
        "no_command": "<b>⚠️ | Please provide a command to execute</b>",
        "timeout": "<b>⏱️ | Command execution timeout (60s)</b>",
    }

    @loader.command()
    async def sh(self, mx, event):
        """Execute shell command
        Usage: .sh <command>"""
        
        args = await utils.get_args_raw(mx, event)
        
        if not args:
            await utils.answer(mx, self.strings.get("no_command"))
            return
        
        await utils.answer(mx, self.strings.get("executing"))
        
        try:
            process = await asyncio.create_subprocess_shell(
                args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=60.0
                )
            except asyncio.TimeoutError:
                process.kill()
                await utils.answer(mx, self.strings.get("timeout"))
                return
            
            output = stdout.decode('utf-8', errors='replace')
            error = stderr.decode('utf-8', errors='replace')
            
            result = output if output else error
            
            if not result:
                result = "Command executed successfully (no output)"
            if len(result) > 4000:
                result = result[:4000] + "\n... (output truncated)"
            
            result_escaped = html.escape(result)
            command_escaped = html.escape(args)
            
            await utils.answer(
                mx,
                self.strings.get("result").format(command_escaped, result_escaped)
            )
            
        except Exception as e:
            await utils.answer(
                mx,
                self.strings.get("error").format(html.escape(str(e)))
            )
