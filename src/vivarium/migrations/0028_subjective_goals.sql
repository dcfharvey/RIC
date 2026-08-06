CREATE TABLE subjective_goal (
 id INTEGER PRIMARY KEY, public_id TEXT NOT NULL UNIQUE, world_id INTEGER NOT NULL, character_id INTEGER NOT NULL,
 goal_key TEXT NOT NULL, family TEXT NOT NULL CHECK (family IN ('immediate','persistent','social','defensive','collective')),
 target_json TEXT NOT NULL CHECK (json_type(target_json) = 'object'), source_kind TEXT NOT NULL,
 horizon_at TEXT, success_conditions_json TEXT NOT NULL CHECK (json_type(success_conditions_json) = 'object'),
 perceived_feasibility_milli INTEGER NOT NULL CHECK (perceived_feasibility_milli BETWEEN 0 AND 1000),
 importance_milli INTEGER NOT NULL CHECK (importance_milli BETWEEN 0 AND 1000), urgency_milli INTEGER NOT NULL CHECK (urgency_milli BETWEEN 0 AND 1000),
 status TEXT NOT NULL CHECK (status IN ('candidate','adopted','abandoned','completed')), created_at TEXT NOT NULL,
 UNIQUE(world_id, character_id, goal_key), FOREIGN KEY(world_id, character_id) REFERENCES character(world_id,id));
CREATE TABLE subjective_intention (
 id INTEGER PRIMARY KEY, public_id TEXT NOT NULL UNIQUE, world_id INTEGER NOT NULL, character_id INTEGER NOT NULL, goal_id INTEGER NOT NULL REFERENCES subjective_goal(id),
 intention_key TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('active','interrupted','completed','abandoned')),
 plan_json TEXT NOT NULL CHECK(json_type(plan_json)='object'), resume_context_json TEXT NOT NULL CHECK(json_type(resume_context_json)='object'), created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
 UNIQUE(world_id, character_id, intention_key));
CREATE UNIQUE INDEX subjective_one_active_intention ON subjective_intention(world_id,character_id) WHERE status='active';
CREATE TABLE subjective_goal_event (id INTEGER PRIMARY KEY, world_id INTEGER NOT NULL, character_id INTEGER NOT NULL, goal_id INTEGER REFERENCES subjective_goal(id), intention_id INTEGER REFERENCES subjective_intention(id), event_type TEXT NOT NULL, payload_json TEXT NOT NULL CHECK(json_type(payload_json)='object'), recorded_at TEXT NOT NULL);
CREATE TRIGGER subjective_goal_no_delete BEFORE DELETE ON subjective_goal BEGIN SELECT RAISE(ABORT,'subjective goal cannot be deleted'); END;
CREATE TRIGGER subjective_intention_no_delete BEFORE DELETE ON subjective_intention BEGIN SELECT RAISE(ABORT,'subjective intention cannot be deleted'); END;
