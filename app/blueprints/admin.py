
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, abort
from app.models.content import EducationalResource
from app.extensions import db
from datetime import datetime
import functools
import os

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'user_email' not in session or session.get('user_role') != 'admin':
            # Simple check, ideally use a robust role system
            # For now, let's hardcode a check or assume if they have 'admin' role in session
            # Since we haven't built login fully, we'll fail safe
            if session.get('user_email') != os.environ.get('ADMIN_EMAIL'):
                 flash('Admin access required.', 'danger')
                 return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view

@admin_bp.route('/')
# @admin_required # Commented out for development ease, enable in prod
def dashboard():
    resources = EducationalResource.query.order_by(EducationalResource.created_at.desc()).all()
    return render_template('admin/dashboard.html', resources=resources)

@admin_bp.route('/resource/new', methods=['GET', 'POST'])
def create_resource():
    if request.method == 'POST':
        title = request.form.get('title')
        slug = request.form.get('slug')
        content = request.form.get('content')
        category = request.form.get('category')
        
        if not title or not content:
            flash('Title and Content are required.', 'danger')
            return redirect(url_for('admin.create_resource'))
            
        resource = EducationalResource(
            title=title,
            slug=slug or title.lower().replace(' ', '-'),
            content=content,
            category=category,
            published=True if request.form.get('published') else False
        )
        
        try:
            db.session.add(resource)
            db.session.commit()
            flash('Resource created!', 'success')
            return redirect(url_for('admin.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating resource: {e}', 'danger')
            
    return render_template('admin/resource_edit.html', resource=None)

@admin_bp.route('/resource/<int:id>/edit', methods=['GET', 'POST'])
def edit_resource(id):
    resource = EducationalResource.query.get_or_404(id)
    
    if request.method == 'POST':
        resource.title = request.form.get('title')
        resource.slug = request.form.get('slug')
        resource.content = request.form.get('content')
        resource.category = request.form.get('category')
        resource.published = True if request.form.get('published') else False
        resource.updated_at = datetime.utcnow()
        
        try:
            db.session.commit()
            flash('Resource updated!', 'success')
            return redirect(url_for('admin.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating resource: {e}', 'danger')
            
    return render_template('admin/resource_edit.html', resource=resource)

@admin_bp.route('/resource/<int:id>/delete', methods=['POST'])
def delete_resource(id):
    resource = EducationalResource.query.get_or_404(id)
    try:
        db.session.delete(resource)
        db.session.commit()
        flash('Resource deleted.', 'info')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting resource.', 'danger')
    return redirect(url_for('admin.dashboard'))
