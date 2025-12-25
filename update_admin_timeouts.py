"""Script to update admin command delete timeouts to 60 seconds"""
import re

with open('bot.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find AdminCog class and its methods
admin_start = content.find('class AdminCog')
if admin_start == -1:
    print("AdminCog not found!")
    exit()

# Find end of AdminCog (next class or end of file)
admin_end = content.find('\nclass ', admin_start + 1)
if admin_end == -1:
    admin_end = len(content)

admin_section = content[admin_start:admin_end]

# Replace all send_ephemeral_auto_delete calls that don't have delete_after
# Pattern: send_ephemeral_auto_delete(interaction, embed=...) -> add delete_after=60
pattern = r'await send_ephemeral_auto_delete\(interaction, embed=([^)]+)\)'

def replacer(match):
    args = match.group(1)
    if 'delete_after=' in args:
        return match.group(0)  # Already has delete_after
    return f'await send_ephemeral_auto_delete(interaction, embed={args}, delete_after=60)'

new_admin_section = re.sub(pattern, replacer, admin_section)

# Also handle msg = await send_ephemeral_auto_delete(...)
pattern2 = r'msg = await send_ephemeral_auto_delete\(interaction, embed=([^)]+)\)'
def replacer2(match):
    args = match.group(1)
    if 'delete_after=' in args:
        return match.group(0)
    return f'msg = await send_ephemeral_auto_delete(interaction, embed={args}, delete_after=60)'

new_admin_section = re.sub(pattern2, replacer2, new_admin_section)

# Count changes
original_count = admin_section.count('send_ephemeral_auto_delete')
new_count = new_admin_section.count('delete_after=60')
print(f"Found {original_count} send_ephemeral_auto_delete calls in AdminCog")
print(f"Added delete_after=60 to {new_count} calls")

# Replace in content
new_content = content[:admin_start] + new_admin_section + content[admin_end:]

with open('bot.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Done!")
