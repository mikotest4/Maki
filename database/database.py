import motor, asyncio
import motor.motor_asyncio
import time
import pymongo, os
from config import DB_URI, DB_NAME
import logging
from datetime import datetime, timedelta

dbclient = pymongo.MongoClient(DB_URI)
database = dbclient[DB_NAME]

logging.basicConfig(level=logging.INFO)

default_verify = {
    'is_verified': False,
    'verified_time': 0,
    'verify_token': "",
    'link': ""
}

def new_user(id):
    return {
        '_id': id,
        'verify_status': {
            'is_verified': False,
            'verified_time': "",
            'verify_token': "",
            'link': ""
        }
    }

class Yae_X_Miko:

    def __init__(self, DB_URI, DB_NAME):
        self.dbclient = motor.motor_asyncio.AsyncIOMotorClient(DB_URI)
        self.database = self.dbclient[DB_NAME]

        self.channel_data = self.database['channels']
        self.admins_data = self.database['admins']
        self.user_data = self.database['users']
        self.sex_data = self.database['sex']
        self.banned_user_data = self.database['banned_user']
        self.autho_user_data = self.database['autho_user']
        self.del_timer_data = self.database['del_timer']
        self.fsub_data = self.database['fsub']   
        self.rqst_fsub_data = self.database['request_forcesub']
        self.rqst_fsub_Channel_data = self.database['request_forcesub_channel']
        

    # USER DATA
    async def present_user(self, user_id: int):
        found = await self.user_data.find_one({'_id': user_id})
        return bool(found)

    async def add_user(self, user_id: int):
        await self.user_data.insert_one({'_id': user_id})
        return

    async def full_userbase(self):
        user_docs = await self.user_data.find().to_list(length=None)
        user_ids = [doc['_id'] for doc in user_docs]
        return user_ids

    async def del_user(self, user_id: int):
        await self.user_data.delete_one({'_id': user_id})
        return

    # ADMIN DATA
    async def admin_exist(self, admin_id: int):
        found = await self.admins_data.find_one({'_id': admin_id})
        return bool(found)

    async def add_admin(self, admin_id: int):
        if not await self.admin_exist(admin_id):
            await self.admins_data.insert_one({'_id': admin_id})
            return

    async def del_admin(self, admin_id: int):
        if await self.admin_exist(admin_id):
            await self.admins_data.delete_one({'_id': admin_id})
            return

    async def get_all_admins(self):
        users_docs = await self.admins_data.find().to_list(length=None)
        user_ids = [doc['_id'] for doc in users_docs]
        return user_ids

    # BAN USER DATA
    async def ban_user_exist(self, user_id: int):
        found = await self.banned_user_data.find_one({'_id': user_id})
        return bool(found)

    async def add_ban_user(self, user_id: int):
        if not await self.ban_user_exist(user_id):
            await self.banned_user_data.insert_one({'_id': user_id})
            return

    async def del_ban_user(self, user_id: int):
        if await self.ban_user_exist(user_id):
            await self.banned_user_data.delete_one({'_id': user_id})
            return

    async def get_ban_users(self):
        users_docs = await self.banned_user_data.find().to_list(length=None)
        user_ids = [doc['_id'] for doc in users_docs]
        return user_ids

    # AUTO DELETE TIMER SETTINGS
    async def set_del_timer(self, value: int):        
        existing = await self.del_timer_data.find_one({})
        if existing:
            await self.del_timer_data.update_one({}, {'$set': {'value': value}})
        else:
            await self.del_timer_data.insert_one({'value': value})

    async def get_del_timer(self):
        data = await self.del_timer_data.find_one({})
        if data:
            return data.get('value', 600)
        return 0

    # CHANNEL MANAGEMENT
    async def channel_exist(self, channel_id: int):
        found = await self.fsub_data.find_one({'_id': channel_id})
        return bool(found)

    async def add_channel(self, channel_id: int):
        if not await self.channel_exist(channel_id):
            await self.fsub_data.insert_one({'_id': channel_id})
            return

    async def rem_channel(self, channel_id: int):
        if await self.channel_exist(channel_id):
            await self.fsub_data.delete_one({'_id': channel_id})
            return

    async def show_channels(self):
        channel_docs = await self.fsub_data.find().to_list(length=None)
        channel_ids = [doc['_id'] for doc in channel_docs]
        return channel_ids

    # Get current mode of a channel
    async def get_channel_mode(self, channel_id: int):
        data = await self.fsub_data.find_one({'_id': channel_id})
        return data.get("mode", "off") if data else "off"

    # Set mode of a channel
    async def set_channel_mode(self, channel_id: int, mode: str):
        await self.fsub_data.update_one(
            {'_id': channel_id},
            {'$set': {'mode': mode}},
            upsert=True
        )

    # REQUEST FORCE SUB FUNCTIONS
    async def reqChannel_exist(self, channel_id: int):
        found = await self.rqst_fsub_Channel_data.find_one({'channel_id': channel_id})
        return bool(found)

    async def add_reqChannel(self, channel_id: int):
        if not await self.reqChannel_exist(channel_id):
            await self.rqst_fsub_Channel_data.insert_one({'channel_id': channel_id})

    async def del_reqChannel(self, channel_id: int):
        if await self.reqChannel_exist(channel_id):
            await self.rqst_fsub_Channel_data.delete_one({'channel_id': channel_id})

    async def req_user_exist(self, channel_id: int, user_id: int):
        found = await self.rqst_fsub_data.find_one({'channel_id': channel_id, 'user_id': user_id})
        return bool(found)

    async def req_user(self, channel_id: int, user_id: int):
        if not await self.req_user_exist(channel_id, user_id):
            await self.rqst_fsub_data.insert_one({'channel_id': channel_id, 'user_id': user_id})

    async def del_req_user(self, channel_id: int, user_id: int):
        if await self.req_user_exist(channel_id, user_id):
            await self.rqst_fsub_data.delete_one({'channel_id': channel_id, 'user_id': user_id})

    # VERIFICATION SYSTEM - FIXED VERSION
    async def get_verify_status(self, user_id: int):
        """Get verification status for a user with proper error handling"""
        try:
            default = {
                'is_verified': False,
                'verified_time': 0,
                'verify_token': "",
                'link': ""
            }
            
            data = await self.sex_data.find_one({'user_id': user_id})
            if data:
                # Return the stored data or default values if keys are missing
                return {
                    'is_verified': data.get('is_verified', False),
                    'verified_time': data.get('verified_time', 0),
                    'verify_token': data.get('verify_token', ""),
                    'link': data.get('link', "")
                }
            else:
                # Create new user with default values
                await self.sex_data.insert_one({
                    'user_id': user_id,
                    **default
                })
                return default
        except Exception as e:
            logging.error(f"Error getting verify status for user {user_id}: {e}")
            return default_verify

    async def update_verify_status(self, user_id: int, **kwargs):
        """Update verification status with proper error handling and logging"""
        try:
            # Add debug logging
            logging.info(f"Updating verify status for user {user_id}: {kwargs}")
            
            # Ensure we're updating the right fields
            update_data = {}
            for key, value in kwargs.items():
                if key in ['is_verified', 'verified_time', 'verify_token', 'link']:
                    update_data[key] = value
            
            # Upsert the document
            result = await self.sex_data.update_one(
                {'user_id': user_id},
                {'$set': update_data},
                upsert=True
            )
            
            # Log the result
            if result.upserted_id:
                logging.info(f"Created new verify record for user {user_id}")
            elif result.modified_count > 0:
                logging.info(f"Updated verify record for user {user_id}")
            else:
                logging.warning(f"No changes made to verify record for user {user_id}")
                
            return True
        except Exception as e:
            logging.error(f"Error updating verify status for user {user_id}: {e}")
            return False

    async def get_verify_count(self, user_id: int):
        """Get verification count for a user"""
        try:
            data = await self.sex_data.find_one({'user_id': user_id})
            if data:
                return data.get('verify_count', 0)
            return 0
        except Exception as e:
            logging.error(f"Error getting verify count for user {user_id}: {e}")
            return 0

    async def set_verify_count(self, user_id: int, count: int):
        """Set verification count for a user"""
        try:
            await self.sex_data.update_one(
                {'user_id': user_id},
                {'$set': {'verify_count': count}},
                upsert=True
            )
            return True
        except Exception as e:
            logging.error(f"Error setting verify count for user {user_id}: {e}")
            return False

    async def reset_all_verify_counts(self):
        """Reset verification counts for all users"""
        try:
            result = await self.sex_data.update_many(
                {},
                {'$set': {'verify_count': 0}}
            )
            logging.info(f"Reset verify counts for {result.modified_count} users")
            return result.modified_count
        except Exception as e:
            logging.error(f"Error resetting verify counts: {e}")
            return 0

    # DEBUG FUNCTIONS - ADD THESE FOR TROUBLESHOOTING
    async def debug_verify_status(self, user_id: int):
        """Debug function to check verification status"""
        try:
            data = await self.sex_data.find_one({'user_id': user_id})
            logging.info(f"Debug verify status for user {user_id}: {data}")
            return data
        except Exception as e:
            logging.error(f"Error in debug verify status: {e}")
            return None

    async def cleanup_invalid_verify_tokens(self):
        """Clean up invalid or expired verification tokens"""
        try:
            current_time = time.time()
            # Remove tokens older than VERIFY_EXPIRE
            from config import VERIFY_EXPIRE
            cutoff_time = current_time - VERIFY_EXPIRE
            
            result = await self.sex_data.update_many(
                {
                    'verified_time': {'$lt': cutoff_time},
                    'is_verified': True
                },
                {'$set': {'is_verified': False, 'verify_token': ""}}
            )
            
            logging.info(f"Cleaned up {result.modified_count} expired verification tokens")
            return result.modified_count
        except Exception as e:
            logging.error(f"Error cleaning up verify tokens: {e}")
            return 0

# Create database instance
db = Yae_X_Miko(DB_URI, DB_NAME)
