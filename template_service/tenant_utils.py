"""
Template Distribution Utilities - Service 1
Only handles framework template copying, not tenant provisioning
"""

from django.db import connections
from templates.models import Framework, Domain, Category, Subcategory, Control
from company_compliance.models import (
    CompanyFramework,
    CompanyDomain,
    CompanyCategory,
    CompanySubcategory,
    CompanyControl,
)

from template_service.database_router import set_current_tenant, clear_current_tenant, get_current_tenant,tenant_context
from django.db import transaction


def copy_framework_templates_to_tenant(tenant_slug, framework_ids=None):
    """Copy framework templates from main DB to tenant DB with safe context management"""
    print(f"\nStarting template distribution to {tenant_slug}...")

    # Read frameworks from MAIN using context manager
    frameworks = []
    with tenant_context(None):  # Explicit main database context
        if framework_ids is None:
            frameworks = list(Framework.objects.filter(is_active=True))
        elif len(framework_ids) == 0:
            frameworks = []
        else:
            frameworks = list(Framework.objects.filter(id__in=framework_ids, is_active=True))

    count = len(frameworks)
    print(f"Found {count} frameworks to copy")

    if count == 0:
        return []

    # Switch to tenant DB to write using context manager
    copied_frameworks = []
    
    with tenant_context(tenant_slug) as current_tenant:
        if not current_tenant:
            raise ValueError(f"Invalid tenant_slug: {tenant_slug}")
            
        try:
            # Use database transaction for atomicity
            from django.db import transaction
            
            with transaction.atomic():
                for framework in frameworks:
                    print(f"\nCopying framework: {framework.name} v{framework.version}")
                    
                    try:
                        # Check if framework already exists in tenant DB
                        existing = CompanyFramework.objects.filter(
                            name=framework.name, 
                            version=framework.version
                        ).first()

                        if existing:
                            company_framework = existing
                            print(f"   Framework already exists, syncing hierarchy...")
                        else:
                            company_framework = CompanyFramework.objects.create(
                                name=framework.name,
                                full_name=framework.full_name,
                                version=framework.version,
                                template_framework_id=framework.id,
                                description=framework.description
                            )
                            print(f"   Created company framework: {company_framework.name}")

                        # Copy hierarchy with explicit context
                        result = copy_framework_hierarchy_safe(framework, company_framework, tenant_slug)
                        copied_frameworks.append(result)

                        print(
                            f"   Copied {result['domains']} domains, "
                            f"{result['categories']} categories, "
                            f"{result['subcategories']} subcategories, "
                            f"{result['controls_copied']} controls"
                        )

                    except Exception as e:
                        print(f"   Error copying framework {framework.name}: {e}")
                        # Re-raise to trigger transaction rollback
                        raise
            
            print(f"\nTemplate distribution completed successfully!")
            
        except Exception as e:
            print(f"\nTemplate distribution failed, rolling back: {e}")
            copied_frameworks = []
            raise

    return copied_frameworks
                


def copy_framework_hierarchy(template_framework, company_framework):
    """
    Copy Domains → Categories → Subcategories → Controls
    from MAIN templates to TENANT company_* tables.
    """

    stats = {
        'framework': company_framework,
        'domains': 0,
        'categories': 0,
        'subcategories': 0,
        'controls_copied': 0,
    }

    # Remember tenant context
    current_tenant = get_current_tenant()

    # Read ALL template data in one go (stay in MAIN context)
    clear_current_tenant()
    try:
        # Pull all template objects for this framework from MAIN
        template_domains = list(Domain.objects.filter(
            framework=template_framework, is_active=True
        ).order_by('sort_order'))

        template_categories = list(Category.objects.filter(
            domain__framework=template_framework, is_active=True
        ).select_related('domain').order_by('sort_order'))

        template_subcategories = list(Subcategory.objects.filter(
            category__domain__framework=template_framework, is_active=True
        ).select_related('category__domain').order_by('sort_order'))

        template_controls = list(Control.objects.filter(
            subcategory__category__domain__framework=template_framework, is_active=True
        ).select_related('subcategory__category__domain').order_by('sort_order'))

    finally:
        # Switch back to tenant DB for all writes
        if current_tenant:
            set_current_tenant(current_tenant)

    # Wrap the entire company creation process in transaction
    with transaction.atomic():
        # Maps from template IDs to company entities
        dom_map = {}
        cat_map = {}
        sub_map = {}

        # --- Domains ---
        for d in template_domains:
            try:
                cd, created = CompanyDomain.objects.get_or_create(
                    framework=company_framework,
                    template_domain_id=d.id,
                    defaults={
                        'name': d.name,
                        'code': d.code,
                        'description': d.description,
                        'sort_order': d.sort_order,
                    },
                )
                if not created:
                    # Keep template in sync (optional)
                    cd.name = d.name
                    cd.code = d.code
                    cd.description = d.description
                    cd.sort_order = d.sort_order
                    cd.save(update_fields=['name', 'code', 'description', 'sort_order'])
                else:
                    stats['domains'] += 1

                dom_map[d.id] = cd
            except Exception as e:
                print(f"      Error copying domain {d.code}: {e}")
                continue

        # --- Categories ---
        for c in template_categories:
            parent_cd = dom_map.get(c.domain_id)
            if not parent_cd:
                # Parent domain missing; skip gracefully
                continue

            try:
                cc, created = CompanyCategory.objects.get_or_create(
                    domain=parent_cd,
                    template_category_id=c.id,
                    defaults={
                        'name': c.name,
                        'code': c.code,
                        'description': c.description,
                        'sort_order': c.sort_order,
                    },
                )
                if not created:
                    cc.name = c.name
                    cc.code = c.code
                    cc.description = c.description
                    cc.sort_order = c.sort_order
                    cc.save(update_fields=['name', 'code', 'description', 'sort_order'])
                else:
                    stats['categories'] += 1

                cat_map[c.id] = cc
            except Exception as e:
                print(f"      Error copying category {c.code}: {e}")
                continue

        # --- Subcategories ---
        for s in template_subcategories:
            parent_cc = cat_map.get(s.category_id)
            if not parent_cc:
                # Parent category missing; skip gracefully
                continue

            try:
                cs, created = CompanySubcategory.objects.get_or_create(
                    category=parent_cc,
                    template_subcategory_id=s.id,
                    defaults={
                        'name': s.name,
                        'code': s.code,
                        'description': s.description,
                        'sort_order': s.sort_order,
                    },
                )
                if not created:
                    cs.name = s.name
                    cs.code = s.code
                    cs.description = s.description
                    cs.sort_order = s.sort_order
                    cs.save(update_fields=['name', 'code', 'description', 'sort_order'])
                else:
                    stats['subcategories'] += 1

                sub_map[s.id] = cs
            except Exception as e:
                print(f"      Error copying subcategory {s.code}: {e}")
                continue

        # --- Controls ---
        for tc in template_controls:
            parent_cs = sub_map.get(tc.subcategory_id)
            if not parent_cs:
                # Parent subcategory missing; skip gracefully
                continue

            try:
                # Check if control already exists
                exists = CompanyControl.objects.filter(
                    subcategory=parent_cs, 
                    control_code=tc.control_code
                ).exists()
                
                if exists:
                    continue

                CompanyControl.objects.create(
                    subcategory=parent_cs,
                    template_control_id=tc.id,
                    control_code=tc.control_code,
                    title=tc.title,
                    description=tc.description,
                    objective=tc.objective,
                    control_type=tc.control_type,
                    frequency=tc.frequency,
                    risk_level=tc.risk_level,
                    sort_order=tc.sort_order,
                )
                stats['controls_copied'] += 1
                
            except Exception as e:
                print(f"      Error copying control {tc.control_code}: {e}")
                continue

    return stats


def copy_framework_hierarchy_safe(template_framework, company_framework, tenant_slug):
    """
    Copy hierarchy with explicit context management to prevent context loss
    """
    stats = {
        'framework': company_framework,
        'domains': 0,
        'categories': 0,
        'subcategories': 0,
        'controls_copied': 0,
    }

    # Read ALL template data from main database first
    template_data = {}
    with tenant_context(None):  # Explicit main DB context
        template_data['domains'] = list(Domain.objects.filter(
            framework=template_framework, is_active=True
        ).order_by('sort_order'))

        template_data['categories'] = list(Category.objects.filter(
            domain__framework=template_framework, is_active=True
        ).select_related('domain').order_by('sort_order'))

        template_data['subcategories'] = list(Subcategory.objects.filter(
            category__domain__framework=template_framework, is_active=True
        ).select_related('category__domain').order_by('sort_order'))

        template_data['controls'] = list(Control.objects.filter(
            subcategory__category__domain__framework=template_framework, is_active=True
        ).select_related('subcategory__category__domain').order_by('sort_order'))

    # Now create everything in tenant database with explicit context
    with tenant_context(tenant_slug):
        from django.db import transaction
        with transaction.atomic():
            # Maps from template IDs to company entities
            dom_map = {}
            cat_map = {}
            sub_map = {}

            # Create domains
            for d in template_data['domains']:
                try:
                    cd, created = CompanyDomain.objects.get_or_create(
                        framework=company_framework,
                        template_domain_id=d.id,
                        defaults={
                            'name': d.name,
                            'code': d.code,
                            'description': d.description,
                            'sort_order': d.sort_order,
                        },
                    )
                    if not created:
                        cd.name = d.name
                        cd.code = d.code
                        cd.description = d.description
                        cd.sort_order = d.sort_order
                        cd.save(update_fields=['name', 'code', 'description', 'sort_order'])
                    else:
                        stats['domains'] += 1

                    dom_map[d.id] = cd
                except Exception as e:
                    print(f"      Error copying domain {d.code}: {e}")
                    continue

            # Create categories
            for c in template_data['categories']:
                parent_cd = dom_map.get(c.domain_id)
                if not parent_cd:
                    continue

                try:
                    cc, created = CompanyCategory.objects.get_or_create(
                        domain=parent_cd,
                        template_category_id=c.id,
                        defaults={
                            'name': c.name,
                            'code': c.code,
                            'description': c.description,
                            'sort_order': c.sort_order,
                        },
                    )
                    if not created:
                        cc.name = c.name
                        cc.code = c.code
                        cc.description = c.description
                        cc.sort_order = c.sort_order
                        cc.save(update_fields=['name', 'code', 'description', 'sort_order'])
                    else:
                        stats['categories'] += 1

                    cat_map[c.id] = cc
                except Exception as e:
                    print(f"      Error copying category {c.code}: {e}")
                    continue

            # Create subcategories
            for s in template_data['subcategories']:
                parent_cc = cat_map.get(s.category_id)
                if not parent_cc:
                    continue

                try:
                    cs, created = CompanySubcategory.objects.get_or_create(
                        category=parent_cc,
                        template_subcategory_id=s.id,
                        defaults={
                            'name': s.name,
                            'code': s.code,
                            'description': s.description,
                            'sort_order': s.sort_order,
                        },
                    )
                    if not created:
                        cs.name = s.name
                        cs.code = s.code
                        cs.description = s.description
                        cs.sort_order = s.sort_order
                        cs.save(update_fields=['name', 'code', 'description', 'sort_order'])
                    else:
                        stats['subcategories'] += 1

                    sub_map[s.id] = cs
                except Exception as e:
                    print(f"      Error copying subcategory {s.code}: {e}")
                    continue

            # Create controls
            for tc in template_data['controls']:
                parent_cs = sub_map.get(tc.subcategory_id)
                if not parent_cs:
                    continue

                try:
                    exists = CompanyControl.objects.filter(
                        subcategory=parent_cs, 
                        control_code=tc.control_code
                    ).exists()
                    
                    if exists:
                        continue

                    CompanyControl.objects.create(
                        subcategory=parent_cs,
                        template_control_id=tc.id,
                        control_code=tc.control_code,
                        title=tc.title,
                        description=tc.description,
                        objective=tc.objective,
                        control_type=tc.control_type,
                        frequency=tc.frequency,
                        risk_level=tc.risk_level,
                        sort_order=tc.sort_order,
                    )
                    stats['controls_copied'] += 1
                    
                except Exception as e:
                    print(f"      Error copying control {tc.control_code}: {e}")
                    continue

    return stats